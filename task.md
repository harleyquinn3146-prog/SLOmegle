# Task List: Telegram API Maximization

## 1. Discovery & Navigation 🧭
- [ ] **Bot Commands Menu** (`set_my_commands`): Register commands like `/start`, `/language`, `/next` so they appear in the autocomplete menu.
- [ ] **Persistent Menu Button** (`set_chat_menu_button`): Add a persistent "Menu" button next to the input field for quick access to "New Chat" or "Settings".
- [ ] **Deep Linking** (`/start <payload>`): Support referral links or specific start modes (e.g., `t.me/bot?start=gender_female`).

## 2. Chat Experience & Realism 💬 (SKIPPED)
- [ ] **Chat Actions** (`send_chat_action`): Show "Typing...", "Uploading photo..." status when the partner is active.
- [ ] **Reply Markup**: Ensure `force_reply` or `input_field_placeholder` is used where appropriate.

## 3. Rich Media & Interaction 📸
- [ ] **Stickers**: Ensure full sticker support (already partially done, verify animated/video stickers).
- [ ] **Voice/Video Notes**: Ensure round video messages (`video_note`) are supported.
- [ ] **Polls**: Allow users to send polls to each other (fun icebreaker).
- [ ] **Dice**: Support the generic `send_dice` for random games.

## 4. Administration & Growth 📈
- [ ] **Chat Join Request**: Use `approve_chat_join_request` if we ever add a channel/group component.
## 5. Engagement & Retention 🔔
- [ ] **Message Pinning** (`pin_chat_message`): Pin the "Connected" message so the "End Chat" buttons are always accessible.
- [ ] **Push Notifications**: Ensure critical alerts (like "Partner Found") trigger a loud notification (sound/vibration) even if the user has the chat muted (using `disable_notification=False` explicitly, though it's default).
- [ ] **Service Messages**: Delete "Searching..." messages to clean up the chat history (using `delete_message`).
