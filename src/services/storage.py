"""
Supabase storage service for Habesha Dating Bot
"""
import os
import logging
from datetime import datetime
from typing import Optional
import hashlib

from supabase import create_client
from src.config.settings import Settings
from src.bot.utils.compression import compressor

logger = logging.getLogger(__name__)

class StorageService:
    """Handle file storage in Supabase"""
    
    def __init__(self):
        self.client = create_client(
            Settings.SUPABASE_URL,
            Settings.SUPABASE_SERVICE_KEY or Settings.SUPABASE_KEY
        )
        logger.info("✅ Storage service initialized")
    
    async def upload_profile_photo(self, user_id: str, file_bytes: bytes, filename: str) -> Optional[str]:
        """Upload and compress profile photo"""
        try:
            # Compress image
            compressed_data, metadata = compressor.compress(file_bytes, profile='profile')
            
            # Generate unique filename
            file_hash = hashlib.md5(compressed_data).hexdigest()[:8]
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            safe_filename = f"{user_id}/{timestamp}_{file_hash}.jpg"
            
            # Upload to Supabase Storage
            result = self.client.storage.from_(Settings.PROFILE_PHOTOS_BUCKET).upload(
                path=safe_filename,
                file=compressed_data,
                file_options={"content-type": "image/jpeg"}
            )
            
            # Get public URL
            public_url = self.client.storage.from_(Settings.PROFILE_PHOTOS_BUCKET).get_public_url(safe_filename)
            
            logger.info(f"✅ Profile photo uploaded: {public_url} (saved {metadata['savings_percent']}%)")
            return public_url
            
        except Exception as e:
            logger.error(f"Failed to upload profile photo: {e}")
            return None
    
    async def upload_thumbnail(self, user_id: str, file_bytes: bytes, filename: str) -> Optional[str]:
        """Upload thumbnail version"""
        try:
            # Create thumbnail
            thumbnail_data = compressor.create_thumbnail(file_bytes)
            
            # Generate filename
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            safe_filename = f"{user_id}/thumb_{timestamp}.jpg"
            
            # Upload
            result = self.client.storage.from_(Settings.PROFILE_PHOTOS_BUCKET).upload(
                path=safe_filename,
                file=thumbnail_data,
                file_options={"content-type": "image/jpeg"}
            )
            
            public_url = self.client.storage.from_(Settings.PROFILE_PHOTOS_BUCKET).get_public_url(safe_filename)
            return public_url
            
        except Exception as e:
            logger.error(f"Failed to upload thumbnail: {e}")
            return None
    
    async def upload_receipt(self, user_id: str, file_bytes: bytes, filename: str) -> Optional[str]:
        """Upload payment receipt with compression"""
        try:
            # Compress receipt
            compressed_data, metadata = compressor.compress(file_bytes, profile='receipt')
            
            # Generate filename
            file_hash = hashlib.md5(compressed_data).hexdigest()[:8]
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            safe_filename = f"{user_id}/receipt_{timestamp}_{file_hash}.jpg"
            
            # Upload
            result = self.client.storage.from_(Settings.RECEIPTS_BUCKET).upload(
                path=safe_filename,
                file=compressed_data,
                file_options={"content-type": "image/jpeg"}
            )
            
            public_url = self.client.storage.from_(Settings.RECEIPTS_BUCKET).get_public_url(safe_filename)
            
            logger.info(f"✅ Receipt uploaded: {public_url} (saved {metadata['savings_percent']}%)")
            return public_url
            
        except Exception as e:
            logger.error(f"Failed to upload receipt: {e}")
            return None
    
    async def delete_file(self, bucket: str, file_path: str) -> bool:
        """Delete file from storage"""
        try:
            self.client.storage.from_(bucket).remove([file_path])
            logger.info(f"✅ Deleted {file_path} from {bucket}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            return False
    
    async def get_file_url(self, bucket: str, file_path: str) -> Optional[str]:
        """Get public URL for file"""
        try:
            return self.client.storage.from_(bucket).get_public_url(file_path)
        except Exception as e:
            logger.error(f"Failed to get file URL: {e}")
            return None

# Singleton instance
storage_service = StorageService()