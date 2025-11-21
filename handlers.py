import logging
from telegram import Update
from telegram.ext import ContextTypes
from config import BAD_WORDS
import database as db
from locales import get_text
from keyboards import (
    get_main_menu_keyboard,
    get_chat_keyboard,
    get_queue_keyboard,
    get_interest_keyboard,
    get_captcha_keyboard,
    get_report_keyboard,
    get_report_keyboard,
    get_language_keyboard
)
from telegram import constants

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"User {update.effective_user.id} started the bot.")
    user_id = update.effective_user.id
    lang = await db.get_language(user_id)
    
    # Simple Captcha: Force user to click a button first
    await update.message.reply_text(
        get_text(lang, 'security_check'),
        reply_markup=get_captcha_keyboard(lang),
        parse_mode='Markdown'
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    lang = await db.get_language(user_id)
    await query.answer()

    if query.data == 'captcha_solved':
        await query.edit_message_text(
            get_text(lang, 'welcome'),
            reply_markup=get_main_menu_keyboard(lang),
            parse_mode='Markdown'
        )

    elif query.data == 'start_search':
        if await db.get_partner(user_id):
            await query.edit_message_text(get_text(lang, 'already_in_chat'), reply_markup=get_chat_keyboard(lang))
            return
        
        if await db.is_in_queue(user_id):
            await query.edit_message_text(get_text(lang, 'searching'), reply_markup=get_queue_keyboard(lang), parse_mode='Markdown')
            return

        user_interest = await db.get_interest(user_id)
        partner_id = await db.get_from_queue(user_id, user_interest)
        
        if partner_id:
            await db.create_chat(user_id, partner_id)
            partner_lang = await db.get_language(partner_id)
            
            msg = get_text(lang, 'connected')
            partner_msg = get_text(partner_lang, 'connected')
            
            if user_interest:
                msg += get_text(lang, 'matched_interest', user_interest)
                partner_msg += get_text(partner_lang, 'matched_interest', user_interest)
            
            await query.edit_message_text(msg, reply_markup=get_chat_keyboard(lang), parse_mode='Markdown')
            try:
                # Pin message for user
                await context.bot.pin_chat_message(chat_id=user_id, message_id=query.message.message_id)
            except Exception:
                pass

            try:
                sent_partner = await context.bot.send_message(partner_id, partner_msg, reply_markup=get_chat_keyboard(partner_lang), parse_mode='Markdown')
                # Pin message for partner
                await context.bot.pin_chat_message(chat_id=partner_id, message_id=sent_partner.message_id)
            except Exception as e:
                logger.error(f"Failed to send message to partner {partner_id}: {e}")
            
            # Cleanup searching message
            if 'searching_msg_id' in context.user_data:
                try:
                    await context.bot.delete_message(chat_id=user_id, message_id=context.user_data['searching_msg_id'])
                    del context.user_data['searching_msg_id']
                except Exception:
                    pass
        else:
            await db.add_to_queue(user_id, user_interest)
            msg = get_text(lang, 'searching')
            if user_interest:
                msg += get_text(lang, 'interest_label', user_interest)
            sent_msg = await query.edit_message_text(msg, reply_markup=get_queue_keyboard(lang), parse_mode='Markdown')
            # Store searching message ID for cleanup
            context.user_data['searching_msg_id'] = sent_msg.message_id

    elif query.data == 'set_interest':
        current_interest = await db.get_interest(user_id) or "None"
        await query.edit_message_text(
            get_text(lang, 'select_interest', current_interest),
            reply_markup=get_interest_keyboard(lang),
            parse_mode='Markdown'
        )

    elif query.data.startswith('interest_'):
        interest = query.data.split('_')[1]
        if interest == "Random":
            interest = None
        await db.set_interest(user_id, interest)
        await query.edit_message_text(
            get_text(lang, 'interest_set', interest or 'Random'),
            reply_markup=get_main_menu_keyboard(lang),
            parse_mode='Markdown'
        )
        
    elif query.data == 'set_language':
        await query.edit_message_text(
            get_text(lang, 'select_language'),
            reply_markup=get_language_keyboard(),
            parse_mode='Markdown'
        )
        
    elif query.data.startswith('lang_'):
        new_lang = query.data.split('_')[1]
        await db.set_language(user_id, new_lang)
        lang = new_lang # Update local var for response
        
        await query.edit_message_text(
            get_text(lang, 'lang_set'),
            reply_markup=get_main_menu_keyboard(lang),
            parse_mode='Markdown'
        )

    elif query.data == 'main_menu':
        await query.edit_message_text(
            get_text(lang, 'welcome'),
            reply_markup=get_main_menu_keyboard(lang),
            parse_mode='Markdown'
        )

    elif query.data == 'stop_chat':
        partner_id = await db.end_chat(user_id)
        await context.bot.unpin_all_chat_messages(chat_id=user_id)
        await query.edit_message_text(get_text(lang, 'chat_ended'), reply_markup=get_main_menu_keyboard(lang), parse_mode='Markdown')
        if partner_id:
            partner_lang = await db.get_language(partner_id)
            try:
                await context.bot.send_message(partner_id, get_text(partner_lang, 'partner_disconnected'), reply_markup=get_main_menu_keyboard(partner_lang), parse_mode='Markdown')
            except Exception as e:
                logger.error(f"Failed to notify partner {partner_id}: {e}")

    elif query.data == 'next_partner':
        partner_id = await db.end_chat(user_id)
        await context.bot.unpin_all_chat_messages(chat_id=user_id)
        if partner_id:
            partner_lang = await db.get_language(partner_id)
            try:
                await context.bot.send_message(partner_id, get_text(partner_lang, 'partner_disconnected'), reply_markup=get_main_menu_keyboard(partner_lang), parse_mode='Markdown')
            except Exception as e:
                logger.error(f"Failed to notify partner {partner_id}: {e}")
        
        # Start new search immediately
        user_interest = await db.get_interest(user_id)
        partner_id = await db.get_from_queue(user_id, user_interest)
        
        if partner_id:
            await db.create_chat(user_id, partner_id)
            partner_lang = await db.get_language(partner_id)
            
            msg = get_text(lang, 'connected')
            partner_msg = get_text(partner_lang, 'connected')
            
            if user_interest:
                msg += get_text(lang, 'matched_interest', user_interest)
                partner_msg += get_text(partner_lang, 'matched_interest', user_interest)
            
            await query.edit_message_text(msg, reply_markup=get_chat_keyboard(lang), parse_mode='Markdown')
            try:
                # Pin message for user
                await context.bot.pin_chat_message(chat_id=user_id, message_id=query.message.message_id)
            except Exception:
                pass

            try:
                sent_partner = await context.bot.send_message(partner_id, partner_msg, reply_markup=get_chat_keyboard(partner_lang), parse_mode='Markdown')
                # Pin message for partner
                await context.bot.pin_chat_message(chat_id=partner_id, message_id=sent_partner.message_id)
            except Exception as e:
                logger.error(f"Failed to send message to partner {partner_id}: {e}")
            
            # Cleanup searching message
            if 'searching_msg_id' in context.user_data:
                try:
                    await context.bot.delete_message(chat_id=user_id, message_id=context.user_data['searching_msg_id'])
                    del context.user_data['searching_msg_id']
                except Exception:
                    pass
        else:
            await db.add_to_queue(user_id, user_interest)
            msg = get_text(lang, 'searching')
            if user_interest:
                msg += get_text(lang, 'interest_label', user_interest)
            sent_msg = await query.edit_message_text(msg, reply_markup=get_queue_keyboard(lang), parse_mode='Markdown')
            context.user_data['searching_msg_id'] = sent_msg.message_id

    elif query.data == 'cancel_search':
        await db.remove_from_queue(user_id)
        # Cleanup searching message
        if 'searching_msg_id' in context.user_data:
            try:
                await context.bot.delete_message(chat_id=user_id, message_id=context.user_data['searching_msg_id'])
                del context.user_data['searching_msg_id']
            except Exception:
                pass
        await query.message.reply_text(get_text(lang, 'search_cancelled'), reply_markup=get_main_menu_keyboard(lang), parse_mode='Markdown')

    elif query.data == 'help':
        await query.edit_message_text(
            get_text(lang, 'help_text'),
            reply_markup=get_main_menu_keyboard(lang),
            parse_mode='Markdown'
        )
    
    elif query.data == 'report_menu':
        await query.edit_message_text(get_text(lang, 'report_menu'), reply_markup=get_report_keyboard(lang))

    elif query.data.startswith('report_'):
        reason = query.data.split('_')[1]
        partner_id = await db.get_partner(user_id)
        if partner_id:
            await db.report_user(user_id, partner_id, reason)
            await query.answer(get_text(lang, 'user_reported'), show_alert=True)
            await query.edit_message_text(get_text(lang, 'report_submitted'), reply_markup=get_chat_keyboard(lang), parse_mode='Markdown')
        else:
            await query.answer(get_text(lang, 'not_in_chat'), show_alert=True)
            await query.edit_message_text(get_text(lang, 'use_menu'), reply_markup=get_main_menu_keyboard(lang))

    elif query.data == 'back_to_chat':
         await query.edit_message_text(get_text(lang, 'chat_title'), reply_markup=get_chat_keyboard(lang), parse_mode='Markdown')

    elif query.data == 'block_partner':
        partner_id = await db.end_chat(user_id)
        if partner_id:
            await db.block_user(user_id, partner_id)
            await query.edit_message_text(get_text(lang, 'blocked'), reply_markup=get_main_menu_keyboard(lang), parse_mode='Markdown')
            partner_lang = await db.get_language(partner_id)
            try:
                await context.bot.send_message(partner_id, get_text(partner_lang, 'partner_disconnected'), reply_markup=get_main_menu_keyboard(partner_lang), parse_mode='Markdown')
            except Exception as e:
                logger.error(f"Failed to notify partner {partner_id}: {e}")
        else:
             await query.edit_message_text(get_text(lang, 'not_in_chat'), reply_markup=get_main_menu_keyboard(lang))


from middleware import check_rate_limit
import asyncio
from telegram import InputMediaPhoto, InputMediaVideo, InputMediaAudio, InputMediaDocument

# Buffer for media groups: media_group_id -> list of messages
media_buffer = {}

async def send_media_group_task(context, partner_id, media_group_id):
    """Wait for all media in a group to arrive, then send them together."""
    await asyncio.sleep(2)  # Wait 2 seconds for all parts to arrive
    
    messages = media_buffer.pop(media_group_id, [])
    if not messages:
        return
    
    # Sort by message_id to ensure correct order
    messages.sort(key=lambda m: m.message_id)
    
    media = []
    # Use the caption from the first message that has one
    caption = next((m.caption for m in messages if m.caption), None)
    
    for i, msg in enumerate(messages):
        # Only attach caption to the first item
        media_caption = caption if i == 0 else None
        
        if msg.photo:
            media.append(InputMediaPhoto(msg.photo[-1].file_id, caption=media_caption))
        elif msg.video:
            media.append(InputMediaVideo(msg.video.file_id, caption=media_caption))
        elif msg.audio:
            media.append(InputMediaAudio(msg.audio.file_id, caption=media_caption))
        elif msg.document:
            media.append(InputMediaDocument(msg.document.file_id, caption=media_caption))
            
    if media:
        try:
            sent_msgs = await context.bot.send_media_group(chat_id=partner_id, media=media)
            
            # Log all messages
            sender_id = messages[0].from_user.id
            for orig, sent in zip(messages, sent_msgs):
                await db.log_message(sender_id, orig.message_id, partner_id, sent.message_id)
                
        except Exception as e:
            logger.error(f"Failed to send media group to {partner_id}: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = await db.get_language(user_id)
    
    # Rate Limit Check
    is_allowed, error_msg = check_rate_limit(user_id)
    if not is_allowed:
        if "Muted" in error_msg:
            # Extract seconds
            import re
            seconds = re.search(r'\d+', error_msg).group()
            await update.message.reply_text(get_text(lang, 'spam_mute', seconds))
        else:
            await update.message.reply_text(error_msg)
        return

    partner_id = await db.get_partner(user_id)
    
    if partner_id:
        # Bad Word Filter
        if update.message.text:
            text_lower = update.message.text.lower()
            for bad_word in BAD_WORDS:
                if bad_word in text_lower:
                    await update.message.reply_text(get_text(lang, 'blocked_msg'), parse_mode='Markdown')
                    return

        # Media Group Handling
        if update.message.media_group_id:
            mg_id = update.message.media_group_id
            if mg_id not in media_buffer:
                media_buffer[mg_id] = []
                context.application.create_task(send_media_group_task(context, partner_id, mg_id))
            
            media_buffer[mg_id].append(update.message)
            return

        try:
            # Check if this is a reply
            reply_to_message_id = None
            if update.message.reply_to_message:
                reply_to_message_id = await db.get_partner_message_id(user_id, update.message.reply_to_message.message_id)

            sent_msg = await update.message.copy(
                chat_id=partner_id,
                reply_to_message_id=reply_to_message_id
            )
            
            # Log message
            await db.log_message(user_id, update.message.message_id, partner_id, sent_msg.message_id)
            
        except Exception as e:
            logger.error(f"Failed to send message to {partner_id}: {e}")
            # Notify user if partner blocked/stopped
            await db.end_chat(user_id)
            await update.message.reply_text(get_text(lang, 'partner_offline'), reply_markup=get_main_menu_keyboard(lang))
    else:
        # Not in chat
        pass


async def handle_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle edited messages and sync to partner."""
    user_id = update.effective_user.id
    partner_id = await db.get_partner(user_id)
    
    if partner_id and update.edited_message:
        try:
            # Find the corresponding message on partner's side
            # We use get_partner_message_id because we are looking for the message sent TO the partner
            # corresponding to the message sent BY the user (which is update.edited_message)
            partner_msg_id = await db.get_partner_message_id(user_id, update.edited_message.message_id)
            
            if partner_msg_id:
                # Edit the message on partner's side
                if update.edited_message.text:
                    await context.bot.edit_message_text(
                        chat_id=partner_id,
                        message_id=partner_msg_id,
                        text=update.edited_message.text
                    )
                    logger.info(f"Synced edit from {user_id} to {partner_id}")
        except Exception as e:
            logger.error(f"Failed to sync edit: {e}")


async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Allow user to delete a sent message by replying to it with /delete."""
    user_id = update.effective_user.id
    partner_id = await db.get_partner(user_id)
    
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Reply to the message you want to delete with /delete.")
        return

    target_msg_id = update.message.reply_to_message.message_id
    
    # Find the partner's copy of this message
    partner_msg_id = await db.get_partner_message_id(user_id, target_msg_id)
    
    if partner_msg_id and partner_id:
        try:
            await context.bot.delete_message(chat_id=partner_id, message_id=partner_msg_id)
            await update.message.reply_text("🗑️ Message deleted for partner.")
        except Exception as e:
            logger.error(f"Failed to delete message: {e}")
            await update.message.reply_text("⚠️ Failed to delete message (maybe too old?).")
    else:
        await update.message.reply_text("⚠️ Could not find that message to delete.")

async def next_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /next command."""
    user_id = update.effective_user.id
    lang = await db.get_language(user_id)
    
    partner_id = await db.end_chat(user_id)
    await context.bot.unpin_all_chat_messages(chat_id=user_id)
    
    if partner_id:
        partner_lang = await db.get_language(partner_id)
        try:
            await context.bot.send_message(partner_id, get_text(partner_lang, 'partner_disconnected'), reply_markup=get_main_menu_keyboard(partner_lang), parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Failed to notify partner {partner_id}: {e}")
    
    # Start new search immediately
    user_interest = await db.get_interest(user_id)
    partner_id = await db.get_from_queue(user_id, user_interest)
    
    if partner_id:
        await db.create_chat(user_id, partner_id)
        partner_lang = await db.get_language(partner_id)
        
        msg = get_text(lang, 'connected')
        partner_msg = get_text(partner_lang, 'connected')
        
        if user_interest:
            msg += get_text(lang, 'matched_interest', user_interest)
            partner_msg += get_text(partner_lang, 'matched_interest', user_interest)
        
        sent_msg = await update.message.reply_text(msg, reply_markup=get_chat_keyboard(lang), parse_mode='Markdown')
        try:
            # Pin message for user
            await context.bot.pin_chat_message(chat_id=user_id, message_id=sent_msg.message_id)
        except Exception:
            pass

        try:
            sent_partner = await context.bot.send_message(partner_id, partner_msg, reply_markup=get_chat_keyboard(partner_lang), parse_mode='Markdown')
            # Pin message for partner
            await context.bot.pin_chat_message(chat_id=partner_id, message_id=sent_partner.message_id)
        except Exception as e:
            logger.error(f"Failed to send message to partner {partner_id}: {e}")
    else:
        await db.add_to_queue(user_id, user_interest)
        msg = get_text(lang, 'searching')
        if user_interest:
            msg += get_text(lang, 'interest_label', user_interest)
        sent_msg = await update.message.reply_text(msg, reply_markup=get_queue_keyboard(lang), parse_mode='Markdown')
        context.user_data['searching_msg_id'] = sent_msg.message_id

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stop command."""
    user_id = update.effective_user.id
    lang = await db.get_language(user_id)
    
    partner_id = await db.end_chat(user_id)
    await context.bot.unpin_all_chat_messages(chat_id=user_id)
    
    await update.message.reply_text(get_text(lang, 'chat_ended'), reply_markup=get_main_menu_keyboard(lang), parse_mode='Markdown')
    
    if partner_id:
        partner_lang = await db.get_language(partner_id)
        try:
            await context.bot.send_message(partner_id, get_text(partner_lang, 'partner_disconnected'), reply_markup=get_main_menu_keyboard(partner_lang), parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Failed to notify partner {partner_id}: {e}")

async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /language command."""
    user_id = update.effective_user.id
    lang = await db.get_language(user_id)
    await update.message.reply_text(
        get_text(lang, 'select_language'),
        reply_markup=get_language_keyboard(),
        parse_mode='Markdown'
    )
