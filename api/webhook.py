"""
Vercel serverless function for Telegram webhook
"""
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
import telegram
from telegram.ext import Dispatcher
import logging
import os
import sys
from datetime import datetime

# Add project to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.settings import Settings
from src.database.supabase_client import supabase
from src.bot.main import HabeshaDatingBot

# Initialize FastAPI
app = FastAPI()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize bot
bot = telegram.Bot(token=Settings.BOT_TOKEN)
dispatcher = Dispatcher(bot, None, use_context=True)

# Initialize main bot to get handlers
main_bot = HabeshaDatingBot()

@app.on_event("startup")
async def startup_event():
    """Setup on startup"""
    logger.info("🚀 Bot webhook starting up...")
    
    # Set webhook
    webhook_url = f"{Settings.WEBHOOK_URL}"
    await bot.set_webhook(url=webhook_url)
    logger.info(f"✅ Webhook set to {webhook_url}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("👋 Bot shutting down...")
    await bot.delete_webhook()

@app.post("/api/webhook")
async def webhook(request: Request):
    """Handle incoming Telegram updates"""
    try:
        # Parse update
        data = await request.json()
        update = telegram.Update.de_json(data, bot)
        
        # Process update
        dispatcher.process_update(update)
        
        return Response(status_code=200)
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return Response(status_code=500)

@app.get("/api/health")
async def health():
    """Health check endpoint"""
    try:
        # Test database connection
        test = supabase.db('users').select('count', count='exact').execute()
        
        return JSONResponse({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "database": "connected",
            "users": test.count
        })
    except Exception as e:
        return JSONResponse({
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }, status_code=500)

@app.get("/")
async def root():
    """Root endpoint"""
    return JSONResponse({
        "name": "Habesha Dating Bot",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    })

@app.get("/set_webhook")
async def set_webhook_manually():
    """Manually set webhook (for initial setup)"""
    webhook_url = f"{Settings.WEBHOOK_URL}"
    success = await bot.set_webhook(url=webhook_url)
    if success:
        return {"status": "success", "webhook": webhook_url}
    return {"status": "failed"}