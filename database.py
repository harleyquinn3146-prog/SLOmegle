import os
import logging

from config import DB_TYPE

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ----------------------------------------------------------------------
# SQLite implementation (Async version)
# ----------------------------------------------------------------------
if DB_TYPE == "sqlite":
    import aiosqlite
    DB_PATH = "bot.db"

    async def init_db():
        async with aiosqlite.connect(DB_PATH) as conn:
            await conn.execute("""CREATE TABLE IF NOT EXISTS waiting_queue (user_id INTEGER PRIMARY KEY, interest TEXT)""")
            await conn.execute("""CREATE TABLE IF NOT EXISTS active_chats (user_id INTEGER PRIMARY KEY, partner_id INTEGER)""")
            await conn.execute("""CREATE TABLE IF NOT EXISTS user_settings (user_id INTEGER PRIMARY KEY, interest TEXT, language TEXT DEFAULT 'en')""")
            await conn.execute("""CREATE TABLE IF NOT EXISTS blocked_users (user_id INTEGER, blocked_user_id INTEGER, PRIMARY KEY (user_id, blocked_user_id))""")
            await conn.execute("""CREATE TABLE IF NOT EXISTS reports (id INTEGER PRIMARY KEY AUTOINCREMENT, reporter_id INTEGER, reported_id INTEGER, reason TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)""")
            await conn.execute("""CREATE TABLE IF NOT EXISTS message_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, sender_id INTEGER, sender_msg_id INTEGER, receiver_id INTEGER, receiver_msg_id INTEGER, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)""")
            
            # Migration: Add language column if it doesn't exist (for existing databases)
            try:
                await conn.execute("ALTER TABLE user_settings ADD COLUMN language TEXT DEFAULT 'en'")
                await conn.commit()
                logger.info("Migrated database: Added language column to user_settings")
            except Exception as e:
                # Column likely already exists
                pass
            
            await conn.commit()
        logger.info("SQLite DB initialized")

    async def set_interest(user_id, interest):
        async with aiosqlite.connect(DB_PATH) as conn:
            await conn.execute("INSERT INTO user_settings (user_id, interest) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET interest=?", (user_id, interest, interest))
            await conn.commit()
        logger.info(f"User {user_id} set interest to {interest}")

    async def get_language(user_id):
        async with aiosqlite.connect(DB_PATH) as conn:
            async with conn.execute("SELECT language FROM user_settings WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 'en'

    async def set_language(user_id, language):
        async with aiosqlite.connect(DB_PATH) as conn:
            # Upsert logic: ensure user exists, update language
            # We need to preserve interest if it exists, but here we use upsert on user_id
            # If row doesn't exist, interest will be null (which is fine)
            await conn.execute("INSERT INTO user_settings (user_id, language) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET language=?", (user_id, language, language))
            await conn.commit()
        logger.info(f"User {user_id} set language to {language}")

    async def get_interest(user_id):
        async with aiosqlite.connect(DB_PATH) as conn:
            async with conn.execute("SELECT interest FROM user_settings WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
        return row[0] if row else None

    async def add_to_queue(user_id, interest=None):
        async with aiosqlite.connect(DB_PATH) as conn:
            # Ensure interest column exists (migration for existing DB)
            try:
                await conn.execute("ALTER TABLE waiting_queue ADD COLUMN interest TEXT")
            except aiosqlite.OperationalError:
                pass # Column already exists
            
            await conn.execute("INSERT OR IGNORE INTO waiting_queue (user_id, interest) VALUES (?, ?)", (user_id, interest))
            await conn.commit()
        logger.info(f"User {user_id} added to SQLite queue with interest {interest}")

    async def get_from_queue(user_id, interest=None):
        async with aiosqlite.connect(DB_PATH) as conn:
            # Get list of users blocked by this user
            async with conn.execute("SELECT blocked_user_id FROM blocked_users WHERE user_id = ?", (user_id,)) as cursor:
                blocked_by_me = [row[0] for row in await cursor.fetchall()]
            
            # Get list of users who blocked this user
            async with conn.execute("SELECT user_id FROM blocked_users WHERE blocked_user_id = ?", (user_id,)) as cursor:
                blocked_me = [row[0] for row in await cursor.fetchall()]
            
            excluded_ids = set(blocked_by_me + blocked_me + [user_id])
            excluded_ids_placeholder = ','.join('?' for _ in excluded_ids)
            
            query = f"SELECT user_id FROM waiting_queue WHERE user_id NOT IN ({excluded_ids_placeholder})"
            params = list(excluded_ids)
            
            if interest:
                query += " AND interest = ?"
                params.append(interest)
                
            query += " LIMIT 1"
            
            async with conn.execute(query, params) as cursor:
                row = await cursor.fetchone()
            
            if row:
                partner_id = row[0]
                await conn.execute("DELETE FROM waiting_queue WHERE user_id = ?", (partner_id,))
                await conn.commit()
                return partner_id
                
        return None

    async def remove_from_queue(user_id):
        async with aiosqlite.connect(DB_PATH) as conn:
            await conn.execute("DELETE FROM waiting_queue WHERE user_id = ?", (user_id,))
            await conn.commit()
        logger.info(f"User {user_id} removed from SQLite queue")

    async def is_in_queue(user_id):
        async with aiosqlite.connect(DB_PATH) as conn:
            async with conn.execute("SELECT user_id FROM waiting_queue WHERE user_id = ?", (user_id,)) as cursor:
                exists = await cursor.fetchone() is not None
        return exists

    async def create_chat(user_id, partner_id):
        async with aiosqlite.connect(DB_PATH) as conn:
            await conn.execute("INSERT OR REPLACE INTO active_chats VALUES (?, ?)", (user_id, partner_id))
            await conn.execute("INSERT OR REPLACE INTO active_chats VALUES (?, ?)", (partner_id, user_id))
            await conn.commit()
        logger.info(f"SQLite chat created between {user_id} and {partner_id}")

    async def get_partner(user_id):
        async with aiosqlite.connect(DB_PATH) as conn:
            async with conn.execute("SELECT partner_id FROM active_chats WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
        return row[0] if row else None

    async def end_chat(user_id):
        partner_id = await get_partner(user_id)
        if partner_id:
            async with aiosqlite.connect(DB_PATH) as conn:
                await conn.execute("DELETE FROM active_chats WHERE user_id = ?", (user_id,))
                await conn.execute("DELETE FROM active_chats WHERE user_id = ?", (partner_id,))
                await conn.commit()
            logger.info(f"SQLite chat ended between {user_id} and {partner_id}")
        return partner_id

    async def block_user(user_id, blocked_user_id):
        async with aiosqlite.connect(DB_PATH) as conn:
            await conn.execute("INSERT OR IGNORE INTO blocked_users (user_id, blocked_user_id) VALUES (?, ?)", (user_id, blocked_user_id))
            await conn.commit()
        logger.info(f"User {user_id} blocked {blocked_user_id}")

    async def report_user(reporter_id, reported_id, reason):
        async with aiosqlite.connect(DB_PATH) as conn:
            await conn.execute("INSERT INTO reports (reporter_id, reported_id, reason) VALUES (?, ?, ?)", (reporter_id, reported_id, reason))
            await conn.commit()
        logger.info(f"User {reporter_id} reported {reported_id} for {reason}")

    async def log_message(sender_id, sender_msg_id, receiver_id, receiver_msg_id):
        async with aiosqlite.connect(DB_PATH) as conn:
            await conn.execute("INSERT INTO message_logs (sender_id, sender_msg_id, receiver_id, receiver_msg_id) VALUES (?, ?, ?, ?)", 
                      (sender_id, sender_msg_id, receiver_id, receiver_msg_id))
            await conn.commit()

    async def get_partner_message_id(sender_id, sender_msg_id):
        # Find the message ID on the receiver's side given the sender's message ID
        async with aiosqlite.connect(DB_PATH) as conn:
            async with conn.execute("SELECT receiver_msg_id FROM message_logs WHERE sender_id = ? AND sender_msg_id = ?", (sender_id, sender_msg_id)) as cursor:
                row = await cursor.fetchone()
        return row[0] if row else None

    async def get_original_message_id(user_id, reply_msg_id):
        # If user_id is replying to reply_msg_id, it means reply_msg_id was sent TO user_id.
        # So we look for a log where receiver_id = user_id AND receiver_msg_id = reply_msg_id.
        # We want the original sender_msg_id to reply to that on the partner's side.
        async with aiosqlite.connect(DB_PATH) as conn:
            async with conn.execute("SELECT sender_msg_id FROM message_logs WHERE receiver_id = ? AND receiver_msg_id = ?", (user_id, reply_msg_id)) as cursor:
                row = await cursor.fetchone()
        return row[0] if row else None

    async def get_stats():
        """Get bot statistics for admin dashboard."""
        async with aiosqlite.connect(DB_PATH) as conn:
            async with conn.execute("SELECT COUNT(DISTINCT user_id) FROM user_settings") as cursor:
                total_users = (await cursor.fetchone())[0]
            
            async with conn.execute("SELECT COUNT(*) FROM active_chats") as cursor:
                active_chats = (await cursor.fetchone())[0] // 2  # Divide by 2 since each chat has 2 entries
            
            async with conn.execute("SELECT COUNT(*) FROM waiting_queue") as cursor:
                in_queue = (await cursor.fetchone())[0]
        
        return {
            'total_users': total_users,
            'active_chats': active_chats,
            'in_queue': in_queue
        }


# ----------------------------------------------------------------------
# Supabase implementation (used when DB_TYPE == "supabase")
# ----------------------------------------------------------------------
else:
    from supabase import create_client, Client
    from config import SUPABASE_URL, SUPABASE_KEY

    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("Supabase URL or Key is missing in environment variables.")
        raise ValueError("Supabase credentials missing.")

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    async def init_db():
        logger.info("Supabase DB assumed to be pre‑created.")
        # Note: You need to add 'interest' column to waiting_queue and create user_settings table in Supabase manually

    async def set_interest(user_id, interest):
        try:
            supabase.table('user_settings').upsert({'user_id': user_id, 'interest': interest}).execute()
            logger.info(f"User {user_id} set interest to {interest}")
        except Exception as e:
            logger.error(f"Error setting interest: {e}")

    async def get_language(user_id):
        try:
            resp = supabase.table('user_settings').select('language').eq('user_id', user_id).execute()
            if resp.data:
                return resp.data[0].get('language', 'en')
            return 'en'
        except Exception as e:
            logger.error(f"Error getting language: {e}")
            return 'en'

    async def set_language(user_id, language):
        try:
            # We need to be careful not to overwrite interest if we use upsert with just language
            # But Supabase upsert usually merges if configured, or we fetch first.
            # Simpler: upsert with user_id and language. 
            # Note: If row doesn't exist, it creates it. If it exists, it updates specified columns? 
            # Supabase-py upsert replaces the row by default unless we specify ignore_duplicates=False (default)
            # To do a partial update, we should check if user exists or use update()
            
            # Try update first
            resp = supabase.table('user_settings').update({'language': language}).eq('user_id', user_id).execute()
            if not resp.data:
                # If no data returned, user might not exist, so insert
                supabase.table('user_settings').insert({'user_id': user_id, 'language': language}).execute()
                
            logger.info(f"User {user_id} set language to {language}")
        except Exception as e:
            logger.error(f"Error setting language: {e}")

    async def get_interest(user_id):
        try:
            resp = supabase.table('user_settings').select('interest').eq('user_id', user_id).execute()
            if resp.data:
                return resp.data[0]['interest']
            return None
        except Exception as e:
            logger.error(f"Error getting interest: {e}")
            return None

    async def add_to_queue(user_id, interest=None):
        try:
            supabase.table('waiting_queue').upsert({'user_id': user_id, 'interest': interest}).execute()
            logger.info(f"User {user_id} added to Supabase queue with interest {interest}")
        except Exception as e:
            logger.error(f"Error adding to queue: {e}")

    async def get_from_queue(user_id, interest=None):
        try:
            # Complex exclusion logic is harder in Supabase via simple client without RPC
            # For now, we will just fetch a candidate and check if blocked in python (less efficient but works)
            # Ideally, use a Postgres function.
            
            # 1. Get blocked users
            blocked_resp = supabase.table('blocked_users').select('blocked_user_id').eq('user_id', user_id).execute()
            blocked_ids = [item['blocked_user_id'] for item in blocked_resp.data]
            
            # 2. Get users who blocked me
            blocked_me_resp = supabase.table('blocked_users').select('user_id').eq('blocked_user_id', user_id).execute()
            blocked_ids.extend([item['user_id'] for item in blocked_me_resp.data])
            
            query = supabase.table('waiting_queue').select('user_id')
            if interest:
                query = query.eq('interest', interest)
            
            # Fetch a few candidates
            resp = query.limit(10).execute()
            
            for candidate in resp.data:
                candidate_id = candidate['user_id']
                if candidate_id != user_id and candidate_id not in blocked_ids:
                    # Found a valid match
                    supabase.table('waiting_queue').delete().eq('user_id', candidate_id).execute()
                    return candidate_id
            
            return None
        except Exception as e:
            logger.error(f"Error getting from queue: {e}")
            return None

    async def remove_from_queue(user_id):
        try:
            supabase.table('waiting_queue').delete().eq('user_id', user_id).execute()
            logger.info(f"User {user_id} removed from Supabase queue")
        except Exception as e:
            logger.error(f"Error removing from queue: {e}")

    async def is_in_queue(user_id):
        try:
            resp = supabase.table('waiting_queue').select('user_id').eq('user_id', user_id).execute()
            return len(resp.data) > 0
        except Exception as e:
            logger.error(f"Error checking queue status: {e}")
            return False

    async def create_chat(user_id, partner_id):
        try:
            data = [
                {'user_id': user_id, 'partner_id': partner_id},
                {'user_id': partner_id, 'partner_id': user_id}
            ]
            supabase.table('active_chats').upsert(data).execute()
            logger.info(f"Supabase chat created between {user_id} and {partner_id}")
        except Exception as e:
            logger.error(f"Error creating chat: {e}")

    async def get_partner(user_id):
        try:
            resp = supabase.table('active_chats').select('partner_id').eq('user_id', user_id).execute()
            if resp.data:
                return resp.data[0]['partner_id']
            return None
        except Exception as e:
            logger.error(f"Error getting partner: {e}")
            return None

    async def end_chat(user_id):
        try:
            partner_id = await get_partner(user_id)
            if partner_id:
                supabase.table('active_chats').delete().eq('user_id', user_id).execute()
                supabase.table('active_chats').delete().eq('user_id', partner_id).execute()
                logger.info(f"Supabase chat ended between {user_id} and {partner_id}")
            return partner_id
        except Exception as e:
            logger.error(f"Error ending chat: {e}")
            return None

    async def block_user(user_id, blocked_user_id):
        try:
            supabase.table('blocked_users').upsert({'user_id': user_id, 'blocked_user_id': blocked_user_id}).execute()
            logger.info(f"User {user_id} blocked {blocked_user_id}")
        except Exception as e:
            logger.error(f"Error blocking user: {e}")

    async def report_user(reporter_id, reported_id, reason):
        try:
            supabase.table('reports').insert({'reporter_id': reporter_id, 'reported_id': reported_id, 'reason': reason}).execute()
            logger.info(f"User {reporter_id} reported {reported_id}")
        except Exception as e:
            logger.error(f"Error reporting user: {e}")

    async def log_message(sender_id, sender_msg_id, receiver_id, receiver_msg_id):
        try:
            supabase.table('message_logs').insert({
                'sender_id': sender_id,
                'sender_msg_id': sender_msg_id,
                'receiver_id': receiver_id,
                'receiver_msg_id': receiver_msg_id
            }).execute()
        except Exception as e:
            logger.error(f"Error logging message: {e}")

    async def get_partner_message_id(sender_id, sender_msg_id):
        try:
            resp = supabase.table('message_logs').select('receiver_msg_id').eq('sender_id', sender_id).eq('sender_msg_id', sender_msg_id).execute()
            if resp.data:
                return resp.data[0]['receiver_msg_id']
            return None
        except Exception as e:
            logger.error(f"Error getting partner message id: {e}")
            return None

    async def get_original_message_id(user_id, reply_msg_id):
        try:
            resp = supabase.table('message_logs').select('sender_msg_id').eq('receiver_id', user_id).eq('receiver_msg_id', reply_msg_id).execute()
            if resp.data:
                return resp.data[0]['sender_msg_id']
            return None
        except Exception as e:
            logger.error(f"Error getting original message id: {e}")
            return None

    async def get_stats():
        """Get bot statistics for admin dashboard."""
        try:
            # Get total users
            users_resp = supabase.table('user_settings').select('user_id', count='exact').execute()
            total_users = users_resp.count if hasattr(users_resp, 'count') else len(users_resp.data)
            
            # Get active chats
            chats_resp = supabase.table('active_chats').select('user_id', count='exact').execute()
            active_chats = (chats_resp.count if hasattr(chats_resp, 'count') else len(chats_resp.data)) // 2
            
            # Get queue
            queue_resp = supabase.table('waiting_queue').select('user_id', count='exact').execute()
            in_queue = queue_resp.count if hasattr(queue_resp, 'count') else len(queue_resp.data)
            
            return {
                'total_users': total_users,
                'active_chats': active_chats,
                'in_queue': in_queue
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {
                'total_users': 0,
                'active_chats': 0,
                'in_queue': 0
            }



