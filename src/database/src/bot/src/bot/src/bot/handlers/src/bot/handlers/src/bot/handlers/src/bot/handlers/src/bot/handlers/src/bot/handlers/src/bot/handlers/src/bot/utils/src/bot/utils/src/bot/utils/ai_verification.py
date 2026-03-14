"""
AI-powered photo verification for Habesha Dating Bot
"""
import io
import cv2
import numpy as np
from PIL import Image
import logging
from typing import Dict, Tuple
import hashlib

logger = logging.getLogger(__name__)

class AIVerification:
    """AI-powered photo verification"""
    
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_eye.xml'
        )
        self.smile_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_smile.xml'
        )
    
    def verify_photo(self, image_data: bytes) -> Dict:
        """Verify photo authenticity and quality"""
        results = {
            'is_authentic': True,
            'quality_score': 0.0,
            'face_count': 0,
            'has_face': False,
            'is_selfie': False,
            'issues': [],
            'recommendations': [],
            'score': 0
        }
        
        try:
            # Convert to numpy array
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                results['issues'].append('invalid_image')
                results['is_authentic'] = False
                return results
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(50, 50)
            )
            
            results['face_count'] = len(faces)
            results['has_face'] = len(faces) > 0
            
            # Check image quality
            quality_score = self._assess_quality(img)
            results['quality_score'] = quality_score
            
            if quality_score < 0.5:
                results['issues'].append('low_quality')
                results['recommendations'].append('Use a clearer photo with better lighting')
            
            # Check for blur
            if self._is_blurry(gray):
                results['issues'].append('blurry')
                results['recommendations'].append('Photo is blurry, please take a clearer photo')
            
            # Check brightness
            if self._is_dark(gray):
                results['issues'].append('too_dark')
                results['recommendations'].append('Photo is too dark, take photo in good lighting')
            
            # Check if it's a screenshot
            if self._is_screenshot(img):
                results['issues'].append('screenshot')
                results['recommendations'].append('Please upload a real photo, not a screenshot')
                results['is_authentic'] = False
            
            # Check face count
            if results['face_count'] > 1:
                results['issues'].append('multiple_faces')
                results['recommendations'].append('Please upload a photo with only you in it')
                results['is_authentic'] = False
            elif results['face_count'] == 0:
                results['issues'].append('no_face')
                results['recommendations'].append('No face detected, please upload a clear selfie')
                results['is_authentic'] = False
            else:
                # Check if it's a selfie (face close to camera)
                x, y, w, h = faces[0]
                face_area = w * h
                image_area = img.shape[0] * img.shape[1]
                face_ratio = face_area / image_area
                
                # Selfies typically have face taking 10-30% of image
                results['is_selfie'] = 0.1 < face_ratio < 0.3
                
                # Check for eyes (indicates forward-facing)
                roi_gray = gray[y:y+h, x:x+w]
                eyes = self.eye_cascade.detectMultiScale(roi_gray)
                results['has_eyes'] = len(eyes) >= 2
            
            # Calculate overall score (0-100)
            score = 0
            if results['has_face']:
                score += 40
            if results.get('has_eyes', False):
                score += 20
            if results['is_selfie']:
                score += 20
            score += int(results['quality_score'] * 20)
            
            results['score'] = min(score, 100)
            
        except Exception as e:
            logger.error(f"AI verification failed: {e}")
            results['issues'].append('verification_error')
            results['is_authentic'] = False
        
        return results
    
    def _assess_quality(self, img: np.ndarray) -> float:
        """Assess image quality score (0-1)"""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Calculate metrics
        brightness = np.mean(gray)
        contrast = np.std(gray)
        
        # Normalize scores
        brightness_score = min(brightness / 128, 1.0)
        contrast_score = min(contrast / 64, 1.0)
        
        return (brightness_score + contrast_score) / 2
    
    def _is_blurry(self, gray: np.ndarray) -> bool:
        """Detect if image is blurry using Laplacian variance"""
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = laplacian.var()
        
        return variance < 100  # Threshold for blurriness
    
    def _is_dark(self, gray: np.ndarray) -> bool:
        """Detect if image is too dark"""
        mean_brightness = np.mean(gray)
        return mean_brightness < 50
    
    def _is_screenshot(self, img: np.ndarray) -> bool:
        """Detect if image is a screenshot"""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Check for sharp edges (typical of text/UI)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        
        # Check for uniform color blocks
        unique_colors = len(np.unique(img.reshape(-1, img.shape[2]), axis=0))
        color_uniformity = unique_colors < 1000  # Screenshots have fewer colors
        
        return edge_density > 0.3 or color_uniformity

# Global AI verifier instance
ai_verifier = AIVerification()