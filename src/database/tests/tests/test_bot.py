"""
Unit tests for Habesha Dating Bot
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from src.config.settings import Settings
from src.bot.utils.helpers import get_text, validate_age
from src.bot.utils.compression import compressor

class TestSettings:
    """Test configuration settings"""
    
    def test_settings_load(self):
        """Test settings load correctly"""
        assert Settings.BOT_TOKEN is not None
        assert isinstance(Settings.ADMIN_IDS, list)
    
    def test_is_admin(self):
        """Test admin check"""
        # Mock admin IDs
        Settings.ADMIN_IDS = [123456]
        
        assert Settings.is_admin(123456) == True
        assert Settings.is_admin(999999) == False

class TestHelpers:
    """Test helper functions"""
    
    def test_get_text(self):
        """Test translation function"""
        # English
        assert "Welcome" in get_text('welcome', 'en')
        
        # Amharic
        assert "እንኳን" in get_text('welcome', 'am')
        
        # Fallback to English
        assert "Welcome" in get_text('welcome', 'fr')
        
        # Invalid key returns key
        assert get_text('invalid_key') == 'invalid_key'
    
    def test_validate_age(self):
        """Test age validation"""
        assert validate_age(25) == True
        assert validate_age(18) == True
        assert validate_age(100) == True
        assert validate_age(17) == False
        assert validate_age(101) == False

class TestCompression:
    """Test image compression"""
    
    def test_compression_profile(self):
        """Test compression profiles exist"""
        assert 'profile' in compressor.PROFILES
        assert 'thumbnail' in compressor.PROFILES
        assert 'receipt' in compressor.PROFILES
    
    def test_compression_metadata(self):
        """Test compression returns metadata"""
        # Create a simple test image
        from PIL import Image
        import io
        
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        test_image = img_bytes.getvalue()
        
        # Compress
        compressed, metadata = compressor.compress(test_image)
        
        assert 'original_size_kb' in metadata
        assert 'compressed_size_kb' in metadata
        assert 'savings_percent' in metadata