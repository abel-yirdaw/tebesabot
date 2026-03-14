import torch
import torchvision.transforms as transforms
from PIL import Image
import io
import logging
from typing import Dict, Tuple
import numpy as np

logger = logging.getLogger(__name__)

class AIVerification:
    """AI-powered photo verification"""
    
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        # Load pre-trained model for face recognition
        self.model = self._load_model()
        
    def _load_model(self):
        """Load pre-trained model (simplified)"""
        # In production, use a proper face recognition model
        # This is a placeholder
        return None
    
    def verify_photo(self, image_data: bytes) -> Dict:
        """Verify photo authenticity and quality"""
        results = {
            'is_authentic': True,
            'quality_score': 0.0,
            'issues': [],
            'recommendations': []
        }
        
        try:
            img = Image.open(io.BytesIO(image_data))
            
            # Check image quality
            quality_score = self._assess_quality(img)
            results['quality_score'] = quality_score
            
            if quality_score < 0.5:
                results['issues'].append('low_quality')
                results['recommendations'].append('Use a clearer photo with better lighting')
            
            # Check for common issues
            if self._is_blurry(img):
                results['issues'].append('blurry')
                results['recommendations'].append('Photo is blurry, please take a clearer photo')
            
            if self._is_dark(img):
                results['issues'].append('too_dark')
                results['recommendations'].append('Photo is too dark, take photo in good lighting')
            
            # Check if it's a real photo (not screenshot)
            if self._is_screenshot(img):
                results['issues'].append('screenshot')
                results['recommendations'].append('Please upload a real photo, not a screenshot')
                results['is_authentic'] = False
            
            # Check for multiple faces
            face_count = self._count_faces(img)
            if face_count > 1:
                results['issues'].append('multiple_faces')
                results['recommendations'].append('Please upload a photo with only you in it')
                results['is_authentic'] = False
            elif face_count == 0:
                results['issues'].append('no_face')
                results['recommendations'].append('No face detected, please upload a clear selfie')
                results['is_authentic'] = False
            
        except Exception as e:
            logger.error(f"AI verification failed: {e}")
            results['issues'].append('verification_error')
        
        return results
    
    def _assess_quality(self, img: Image.Image) -> float:
        """Assess image quality score (0-1)"""
        # Convert to numpy array
        img_array = np.array(img)
        
        # Calculate metrics
        brightness = np.mean(img_array)
        contrast = np.std(img_array)
        
        # Normalize scores
        brightness_score = min(brightness / 128, 1.0)
        contrast_score = min(contrast / 64, 1.0)
        
        return (brightness_score + contrast_score) / 2
    
    def _is_blurry(self, img: Image.Image) -> bool:
        """Detect if image is blurry using Laplacian variance"""
        img_array = np.array(img.convert('L'))
        laplacian = cv2.Laplacian(img_array, cv2.CV_64F)
        variance = laplacian.var()
        
        return variance < 100  # Threshold for blurriness
    
    def _is_dark(self, img: Image.Image) -> bool:
        """Detect if image is too dark"""
        img_array = np.array(img.convert('L'))
        mean_brightness = np.mean(img_array)
        
        return mean_brightness < 50
    
    def _is_screenshot(self, img: Image.Image) -> bool:
        """Detect if image is a screenshot"""
        img_array = np.array(img)
        
        # Screenshots often have:
        # 1. High sharpness
        # 2. Uniform patterns
        # 3. Specific color distributions
        
        # Check for uniform areas (UI elements)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        
        # Screenshots have high edge density from text/UI
        return edge_density > 0.3
    
    def _count_faces(self, img: Image.Image) -> int:
        """Count faces in image"""
        # Use OpenCV for face detection
        img_array = np.array(img)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        return len(faces)

# Global AI verifier instance
ai_verifier = AIVerification()