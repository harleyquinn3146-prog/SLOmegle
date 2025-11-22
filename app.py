"""
Health check server for Hugging Face Spaces.
This runs alongside the bot to satisfy HF's port 7860 requirement.
"""
from fastapi import FastAPI
import uvicorn
import threading
import sys
import os

# Import the bot
sys.path.insert(0, os.path.dirname(__file__))

app = FastAPI()

@app.get("/")
def health_check():
    return {
        "status": "running",
        "service": "Telegram Omegle Bot",
        "message": "Bot is active and polling for updates"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

def run_bot():
    """Run the Telegram bot in a separate thread"""
    import bot
    # The bot.py script will handle its own execution

if __name__ == "__main__":
    # Start bot in background thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Run FastAPI server on port 7860 (required by HF Spaces)
    uvicorn.run(app, host="0.0.0.0", port=7860)
