#!/usr/bin/env python3
"""
Habesha Dating Bot - Main Entry Point
For local development and PythonAnywhere hosting
"""

import os
import sys
import logging
import asyncio
from datetime import datetime

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import local modules
from src.config.settings import Settings
from src.database.supabase_client import supabase
from src.bot.main import HabeshaDatingBot

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def main():
    """Main async function"""
    logger.info("=" * 60)
    logger.info("🤵 HABESHA DATING BOT")
    logger.info("=" * 60)
    logger.info(f"Starting at: {datetime.now()}")
    logger.info(f"Environment: {Settings.ENV}")
    logger.info(f"Python version: {sys.version}")
    logger.info("=" * 60)
    
    try:
        # Validate settings
        Settings.validate()
        logger.info("✅ Configuration validated")
        
        # Test database connection
        test = supabase.db('users').select('count', count='exact').execute()
        logger.info(f"✅ Database connected: {test.count} users")
        
        # Initialize and run bot
        bot = HabeshaDatingBot()
        
        # Start bot (this blocks until stopped)
        await bot.run()
        
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        return 1
    
    logger.info("👋 Bot shutdown complete")
    return 0

def run():
    """Synchronous wrapper for async main"""
    return asyncio.run(main())

if __name__ == "__main__":
    sys.exit(run())