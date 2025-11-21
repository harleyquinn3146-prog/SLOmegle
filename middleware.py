import time
from collections import defaultdict

# Rate limit settings
RATE_LIMIT_MSG = 5  # Max messages
RATE_LIMIT_WINDOW = 2  # In seconds
MUTE_DURATION = 60  # Seconds

# Storage: user_id -> list of timestamps
user_timestamps = defaultdict(list)
# Storage: user_id -> mute_end_timestamp
muted_users = {}

def check_rate_limit(user_id):
    """
    Check if user is rate limited.
    Returns (is_allowed, error_message)
    """
    now = time.time()
    
    # Check if currently muted
    if user_id in muted_users:
        if now < muted_users[user_id]:
            remaining = int(muted_users[user_id] - now)
            return False, f"⚠️ You are muted for {remaining}s due to spam."
        else:
            del muted_users[user_id]
    
    # Clean old timestamps
    user_timestamps[user_id] = [t for t in user_timestamps[user_id] if now - t < RATE_LIMIT_WINDOW]
    
    # Add current timestamp
    user_timestamps[user_id].append(now)
    
    # Check limit
    if len(user_timestamps[user_id]) > RATE_LIMIT_MSG:
        muted_users[user_id] = now + MUTE_DURATION
        return False, f"🚫 You are sending messages too fast! Muted for {MUTE_DURATION}s."
    
    return True, None
