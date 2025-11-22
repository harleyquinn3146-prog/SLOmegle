# Deploy to Hugging Face Spaces 🤗

This bot can be deployed to Hugging Face Spaces for **free** using Docker.

## Setup Instructions

### 1. Create Space Settings

When creating your Space on Hugging Face:

- **Owner**: `ljackson3146`
- **Space name**: `omeglesl`
- **License**: MIT (or your choice)
- **SDK**: **Docker** ⚠️ (This is critical!)
- **Docker Template**: Choose "Blank Docker template"
- **Hardware**: Free (sufficient for this bot)
- **Visibility**: Public or Private (your choice)

### 2. Configure Environment Variables

After creating the Space, go to **Settings** → **Variables and secrets**:

Add these **secrets**:

| Name | Value |
|------|-------|
| `BOT_TOKEN` | Your Telegram Bot Token from @BotFather |
| `SUPABASE_URL` | Your Supabase Project URL |
| `SUPABASE_KEY` | Your Supabase `service_role` key |
| `DB_TYPE` | `supabase` |
| `ADMIN_IDS` | Your Telegram User ID (e.g., `123456789`) |

> **Important**: These should be added as **Secrets**, not regular variables, to keep them secure.

### 3. Deploy Code

#### Option A: Push from GitHub

1. Link your GitHub repository (`https://github.com/harleyquinn3146-prog/SLOmegle`)
2. Hugging Face will automatically sync and deploy

#### Option B: Direct Git Push

```bash
git remote add hf https://huggingface.co/spaces/ljackson3146/omeglesl
git push hf main
```

### 4. Verify Deployment

1. Go to your Space: `https://huggingface.co/spaces/ljackson3146/omeglesl`
2. Check the **Logs** tab to see if the bot started successfully
3. Look for: `Application started`
4. Test by sending `/start` to your bot on Telegram

## Important Notes

- **No Webhook Setup Needed**: The bot runs in polling mode, perfect for HF Spaces
- **Free Tier**: The free CPU is sufficient for moderate usage
- **Sleeping**: Free Spaces may sleep after inactivity. Upgrade to persistent hardware if needed
- **Database**: All data is stored in Supabase (cloud), so no data loss on restarts

## Troubleshooting

**Bot not responding?**
- Check Logs tab for errors
- Verify environment variables are set correctly
- Ensure Supabase project is active

**Space keeps restarting?**
- Check if `httpx==0.27.2` is in requirements.txt
- Look for Python errors in logs
