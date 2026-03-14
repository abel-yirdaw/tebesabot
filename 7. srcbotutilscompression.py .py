import io
import cv2
import numpy as np
from PIL import Image
import logging
from typing import Tuple, Optional, Dict
import hashlib
import os

logger = logging.getLogger(__name__)

class ImageCompressor:
    """Advanced image compression with multiple algorithms"""
    
    # Compression profiles
    PROFILES = {
        'profile': {
            'max_size_kb': 100,
            'max_dimensions': (800, 800),
            'quality': 85,
            'format': 'JPEG'
        },
        'thumbnail': {
            'max_size_kb': 20,
            'max_dimensions': (200, 200),
            'quality': 75,
            'format': 'JPEG'
        },
        'receipt': {
            'max_size_kb': 50,
            'max_dimensions': (1200, 1200),
            'quality': 70,
            'format': 'JPEG'
        }
    }
    
    @staticmethod
    def detect_face(image_data: bytes) -> Tuple[bool, Dict]:
        """Detect if image contains a face using OpenCV"""
        try:
            # Convert to numpy array
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Load face cascade
            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            return len(faces) > 0, {
                'face_count': len(faces),
                'has_face': len(faces) > 0
            }
        except Exception as e:
            logger.error(f"Face detection failed: {e}")
            return False, {'error': str(e)}
    
    @staticmethod
    def is_selfie(image_data: bytes) -> bool:
        """Detect if image is likely a selfie"""
        try:
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Selfies often have specific characteristics
            height, width = img.shape[:2]
            aspect_ratio = width / height
            
            # Selfies are usually portrait orientation
            is_portrait = height > width
            
            # Check EXIF data for front camera indicators
            # (Simplified - would need more sophisticated detection)
            
            return is_portrait and aspect_ratio < 1
        except:
            return False
    
    @staticmethod
    def compress(
        image_data: bytes,
        profile: str = 'profile',
        maintain_aspect: bool = True
    ) -> Tuple[bytes, Dict]:
        """Compress image with advanced options"""
        
        config = ImageCompressor.PROFILES.get(profile, ImageCompressor.PROFILES['profile'])
        original_size = len(image_data) / 1024
        
        try:
            # Open image
            img = Image.open(io.BytesIO(image_data))
            original_format = img.format
            original_mode = img.mode
            
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = rgb_img
            
            # Calculate new dimensions
            width, height = img.size
            new_width, new_height = width, height
            
            if width > config['max_dimensions'][0] or height > config['max_dimensions'][1]:
                ratio = min(
                    config['max_dimensions'][0] / width,
                    config['max_dimensions'][1] / height
                )
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                
                # Use different resampling based on image size
                if width * height > 2000 * 2000:
                    resample = Image.Resampling.LANCZOS
                else:
                    resample = Image.Resampling.BICUBIC
                
                img = img.resize((new_width, new_height), resample)
            
            # Progressive compression
            output = io.BytesIO()
            quality = config['quality']
            attempts = []
            
            while quality >= 50:
                output.seek(0)
                output.truncate()
                
                # Save with current quality
                img.save(
                    output,
                    format=config['format'],
                    quality=quality,
                    optimize=True,
                    progressive=True
                )
                
                current_size = len(output.getvalue()) / 1024
                attempts.append({
                    'quality': quality,
                    'size_kb': current_size
                })
                
                if current_size <= config['max_size_kb']:
                    break
                
                quality -= 10
            
            # If still too large, create thumbnail
            if len(output.getvalue()) / 1024 > config['max_size_kb']:
                scale = 0.8
                while scale > 0.3:
                    temp_width = int(new_width * scale)
                    temp_height = int(new_height * scale)
                    
                    temp_img = img.resize((temp_width, temp_height), Image.Resampling.LANCZOS)
                    
                    output.seek(0)
                    output.truncate()
                    temp_img.save(
                        output,
                        format=config['format'],
                        quality=70,
                        optimize=True
                    )
                    
                    if len(output.getvalue()) / 1024 <= config['max_size_kb']:
                        break
                    
                    scale -= 0.1
            
            compressed_data = output.getvalue()
            compressed_size = len(compressed_data) / 1024
            
            # Generate hash for deduplication
            image_hash = hashlib.md5(compressed_data).hexdigest()
            
            metadata = {
                'original_size_kb': round(original_size, 2),
                'compressed_size_kb': round(compressed_size, 2),
                'savings_percent': round((1 - compressed_size/original_size) * 100, 2),
                'dimensions': f"{new_width}x{new_height}",
                'format': config['format'],
                'quality_attempts': attempts,
                'hash': image_hash,
                'has_face': ImageCompressor.detect_face(image_data)[0],
                'is_selfie': ImageCompressor.is_selfie(image_data)
            }
            
            logger.info(f"Compression complete: {metadata['savings_percent']}% saved")
            return compressed_data, metadata
            
        except Exception as e:
            logger.error(f"Compression failed: {e}")
            return image_data, {'error': str(e), 'original_size_kb': original_size}
    
    @staticmethod
    def create_thumbnail(image_data: bytes, size: Tuple[int, int] = (200, 200)) -> bytes:
        """Create thumbnail for gallery view"""
        try:
            img = Image.open(io.BytesIO(image_data))
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=75, optimize=True)
            
            return output.getvalue()
        except Exception as e:
            logger.error(f"Thumbnail creation failed: {e}")
            return image_data

# Global compressor instance
compressor = ImageCompressor()