"""
Centralized configuration management for Habesha Dating Bot
"""
import os
from dotenv import load_dotenv
from typing import List
import logging

# Load environment variables
load_dotenv()

class Settings:
    """Configuration settings singleton"""
    
    # Environment
    ENV = os.getenv('ENVIRONMENT', 'development')
    DEBUG = ENV == 'development'
    
    # Telegram
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    BOT_USERNAME = os.getenv('BOT_USERNAME')
    WEBHOOK_URL = os.getenv('WEBHOOK_URL')
    
    # Supabase
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
    
    # Storage Buckets
    PROFILE_PHOTOS_BUCKET = os.getenv('PROFILE_PHOTOS_BUCKET', 'profile-photos')
    RECEIPTS_BUCKET = os.getenv('RECEIPTS_BUCKET', 'payment-receipts')
    
    # Admin
    ADMIN_IDS: List[int] = [int(id) for id in os.getenv('ADMIN_IDS', '').split(',') if id]
    ADMIN_CHANNEL_ID = os.getenv('ADMIN_CHANNEL_ID')
    ADMIN_GROUP_ID = os.getenv('ADMIN_GROUP_ID')
    
    # Payment
    PAYMENT_AMOUNT = int(os.getenv('PAYMENT_AMOUNT', 100))
    PAYMENT_DURATION_DAYS = int(os.getenv('PAYMENT_DURATION_DAYS', 90))
    PAYMENT_METHODS = os.getenv('PAYMENT_METHODS', 'telebirr,cbe,bank').split(',')
    
    # Redis
    REDIS_URL = os.getenv('REDIS_URL')
    
    # Image Settings
    MAX_PHOTOS_PER_USER = 5
    MIN_PHOTOS_REQUIRED = 3
    MAX_PHOTO_SIZE_MB = 5
    COMPRESSED_SIZE_KB = 100
    RECEIPT_COMPRESSED_SIZE_KB = 50
    
    # AI Verification
    ENABLE_AI_VERIFICATION = os.getenv('ENABLE_AI_VERIFICATION', 'true').lower() == 'true'
    
    # Matching
    WEEKLY_LIKES = 5
    SUPERLIKE_COST = 2
    
    # Cache TTL (seconds)
    CACHE_TTL_USER = 3600
    CACHE_TTL_PROFILE = 1800
    
    @classmethod
    def is_admin(cls, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id in cls.ADMIN_IDS
    
    @classmethod
    def validate(cls):
        """Validate required settings"""
        required = ['BOT_TOKEN', 'SUPABASE_URL', 'SUPABASE_KEY']
        missing = [req for req in required if not getattr(cls, req)]
        
        if missing:
            raise ValueError(f"Missing required settings: {', '.join(missing)}")
        
        if not cls.ADMIN_IDS:
            raise ValueError("At least one ADMIN_ID is required")
        
        if not cls.ADMIN_CHANNEL_ID:
            raise ValueError("ADMIN_CHANNEL_ID is required")
        
        return True

# Initialize logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG if Settings.DEBUG else logging.INFO
)
logger = logging.getLogger(__name__)