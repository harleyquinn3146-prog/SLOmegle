# Telegram Omegle Bot

Anonymous text chat bot for Telegram that pairs random users together.

## Features

- Anonymous 1-on-1 text chatting
- Random user pairing
- Simple commands to start/stop chats
- Queue system for waiting users

## Commands

- `/start` - Welcome message
- `/chat` - Join chat queue and get paired
- `/stop` - End current chat
- `/next` - Find new chat partner

## Setup

1. Create bot with @BotFather on Telegram
2. Get bot token
3. Install dependencies:
   ```
   pip install python-telegram-bot supabase
   ```
4. Add token to `config.py`
5. Run: `python bot.py`

## Deployment Options

### Vercel
- Add `vercel.json` config
- Use serverless functions
- Set webhook mode

### Railway
- Connect GitHub repo
- Auto-deploy on push
- Built-in environment variables

### Database - Supabase
- PostgreSQL database
- Real-time subscriptions
- Built-in auth and APIs

## Usage

1. Start the bot with `/start`
2. Use `/chat` to join queue
3. Get paired with random user
4. Chat anonymously
5. Use `/stop` to end or `/next` for new partner

## File Structure

```
├── bot.py          # Main bot logic
├── config.py       # Bot token
├── database.py     # Supabase connection
├── requirements.txt # Dependencies
├── vercel.json     # Vercel config
└── README.md       # This file
```

## How It Works

- Users join a waiting queue with `/chat`
- Bot pairs users when 2+ are waiting
- Messages are forwarded between paired users
- Supabase stores active chats and user data