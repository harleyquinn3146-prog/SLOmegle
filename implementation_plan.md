# Implementation Plan - Telegram API Features

## Goal
Maximize the use of Telegram Bot API features to improve user experience, discovery, and retention.

## Proposed Changes

### 1. Bot Commands & Menu (`bot.py`)
- **Action**: Use `application.bot.set_my_commands` on startup.
- **Commands**:
    - `/start` - Start the bot
    - `/next` - Find next partner
    - `/stop` - End current chat
    - `/language` - Change language
- **Menu Button**: Use `application.bot.set_chat_menu_button` to link to the commands menu or a web app (future).

### 2. Chat Experience (`handlers.py`)
- **Typing Status**:
    - Send `ChatAction.TYPING` when searching.
    - Send `ChatAction.TYPING` before sending the "Connected" message.
- **Pinning**:
    - Pin the "Connected" message upon successful connection.
    - Unpin all messages when chat ends.
- **Cleanup**:
    - Store the `message_id` of the "Searching..." message.
    - Delete it when a partner is found or search is cancelled.

### 3. Notifications (`handlers.py`)
- **Push**: Ensure "Connected" message has `disable_notification=False`.
- **Alerts**: Use `answer_callback_query(text="...", show_alert=True)` for critical errors or confirmations (already partially done).

## Verification Plan
1.  **Startup**: Restart bot, check if "Menu" button appears and "/" shows commands.
2.  **Flow**:
    - Start search -> Verify "Typing..." status.
    - Connect -> Verify "Connected" message is pinned.
    - Connect -> Verify "Searching..." message is deleted.
    - End Chat -> Verify message is unpinned (optional, or just leaves it).
