"""
Supabase database client for Habesha Dating Bot
"""
from supabase import create_client, Client
from src.config.settings import Settings
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class SupabaseClient:
    """Singleton Supabase client with connection pooling"""
    
    _instance: Optional['SupabaseClient'] = None
    _client: Optional[Client] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize Supabase client"""
        try:
            self.client = create_client(
                Settings.SUPABASE_URL,
                Settings.SUPABASE_KEY
            )
            logger.info("✅ Supabase client initialized")
        except Exception as e:
            logger.error(f"❌ Supabase initialization failed: {e}")
            raise
    
    @property
    def db(self):
        """Get database client"""
        return self.client.table
    
    # ========== USER METHODS ==========
    
    def create_user(self, telegram_id: int, **kwargs) -> Optional[Dict]:
        """Create new user"""
        user_data = {
            'telegram_id': telegram_id,
            'username': kwargs.get('username'),
            'first_name': kwargs.get('first_name'),
            'last_name': kwargs.get('last_name'),
            'full_name': kwargs.get('full_name'),
            'age': kwargs.get('age'),
            'gender': kwargs.get('gender'),
            'location': kwargs.get('location'),
            'region': kwargs.get('region'),
            'ethnicity': kwargs.get('ethnicity'),
            'religion': kwargs.get('religion'),
            'occupation': kwargs.get('occupation'),
            'education': kwargs.get('education'),
            'bio': kwargs.get('bio'),
            'looking_for': kwargs.get('looking_for', 'female' if kwargs.get('gender') == 'male' else 'male'),
            'language': kwargs.get('language', 'en'),
            'status': 'pending',
            'weekly_likes': Settings.WEEKLY_LIKES,
            'likes_reset_date': (datetime.utcnow() + timedelta(days=7)).isoformat(),
            'created_at': datetime.utcnow().isoformat()
        }
        
        result = self.db('users').insert(user_data).execute()
        return result.data[0] if result.data else None
    
    def get_user(self, telegram_id: int) -> Optional[Dict]:
        """Get user by telegram ID"""
        result = self.db('users').select('*').eq('telegram_id', telegram_id).execute()
        return result.data[0] if result.data else None
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by database ID"""
        result = self.db('users').select('*').eq('id', user_id).execute()
        return result.data[0] if result.data else None
    
    def update_user(self, telegram_id: int, **kwargs) -> Optional[Dict]:
        """Update user"""
        kwargs['updated_at'] = datetime.utcnow().isoformat()
        result = self.db('users').update(kwargs).eq('telegram_id', telegram_id).execute()
        return result.data[0] if result.data else None
    
    def approve_user(self, user_id: str, admin_id: int) -> Optional[Dict]:
        """Approve user"""
        update_data = {
            'status': 'active',
            'approved_at': datetime.utcnow().isoformat(),
            'approved_by': admin_id,
            'updated_at': datetime.utcnow().isoformat()
        }
        result = self.db('users').update(update_data).eq('id', user_id).execute()
        return result.data[0] if result.data else None
    
    def get_pending_users(self) -> List[Dict]:
        """Get pending users"""
        result = self.db('users').select('*').eq('status', 'pending').execute()
        return result.data if result.data else []
    
    def get_active_users(self) -> List[Dict]:
        """Get active users"""
        result = self.db('users').select('*').eq('status', 'active').execute()
        return result.data if result.data else []
    
    # ========== PHOTO METHODS ==========
    
    def add_photo(self, user_id: str, photo_url: str, thumbnail_url: str = None, is_selfie: bool = True) -> Optional[Dict]:
        """Add photo for verification"""
        photo_data = {
            'user_id': user_id,
            'photo_url': photo_url,
            'thumbnail_url': thumbnail_url,
            'is_selfie': is_selfie,
            'is_approved': False,
            'uploaded_at': datetime.utcnow().isoformat()
        }
        result = self.db('photos').insert(photo_data).execute()
        return result.data[0] if result.data else None
    
    def get_user_photos(self, user_id: str, approved_only: bool = True) -> List[Dict]:
        """Get user photos"""
        query = self.db('photos').select('*').eq('user_id', user_id)
        if approved_only:
            query = query.eq('is_approved', True)
        result = query.execute()
        return result.data if result.data else []
    
    def get_pending_photos(self) -> List[Dict]:
        """Get photos pending verification"""
        result = self.db('photos').select('*, users(full_name, username)').eq('is_approved', False).execute()
        return result.data if result.data else []
    
    def verify_photo(self, photo_id: str, admin_id: int, approved: bool, reason: str = None) -> Optional[Dict]:
        """Verify photo"""
        update_data = {
            'is_approved': approved,
            'approved_by': admin_id,
            'approved_at': datetime.utcnow().isoformat(),
            'rejection_reason': reason
        }
        result = self.db('photos').update(update_data).eq('id', photo_id).execute()
        return result.data[0] if result.data else None
    
    # ========== PAYMENT METHODS ==========
    
    def create_payment(self, user_id: str, receipt_url: str) -> Optional[Dict]:
        """Create payment record"""
        payment_data = {
            'user_id': user_id,
            'receipt_url': receipt_url,
            'amount': Settings.PAYMENT_AMOUNT,
            'duration_days': Settings.PAYMENT_DURATION_DAYS,
            'status': 'pending',
            'created_at': datetime.utcnow().isoformat()
        }
        result = self.db('payments').insert(payment_data).execute()
        return result.data[0] if result.data else None
    
    def get_pending_payments(self) -> List[Dict]:
        """Get pending payments"""
        result = self.db('payments').select('*, users(full_name, username, telegram_id)').eq('status', 'pending').execute()
        return result.data if result.data else []
    
    def approve_payment(self, payment_id: str, admin_id: int) -> Optional[str]:
        """Approve payment and activate subscription"""
        # Update payment
        self.db('payments').update({
            'status': 'approved',
            'processed_by': admin_id,
            'processed_at': datetime.utcnow().isoformat()
        }).eq('id', payment_id).execute()
        
        # Get payment to find user
        payment = self.db('payments').select('user_id').eq('id', payment_id).execute()
        if payment.data:
            user_id = payment.data[0]['user_id']
            
            # Activate subscription
            expiry = datetime.utcnow() + timedelta(days=Settings.PAYMENT_DURATION_DAYS)
            
            self.db('users').update({
                'subscription_active': True,
                'subscription_start': datetime.utcnow().isoformat(),
                'subscription_end': expiry.isoformat(),
                'status': 'active',
                'payment_status': 'paid'
            }).eq('id', user_id).execute()
            
            return user_id
        return None
    
    # ========== MATCHING METHODS ==========
    
    def get_potential_matches(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get potential matches using RPC"""
        try:
            result = self.client.rpc('get_potential_matches', {
                'p_user_id': user_id,
                'p_limit': limit
            }).execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error getting potential matches: {e}")
            return []
    
    def create_like(self, from_user_id: str, to_user_id: str, like_type: str = 'like') -> Dict:
        """Create a like and check for match"""
        # Insert like
        like_data = {
            'from_user_id': from_user_id,
            'to_user_id': to_user_id,
            'like_type': like_type,
            'created_at': datetime.utcnow().isoformat()
        }
        like_result = self.db('likes').insert(like_data).execute()
        
        # Check for mutual like
        mutual = self.db('likes').select('*')\
            .eq('from_user_id', to_user_id)\
            .eq('to_user_id', from_user_id)\
            .execute()
        
        if mutual.data:
            # Create match
            match_data = {
                'user1_id': min(from_user_id, to_user_id),
                'user2_id': max(from_user_id, to_user_id),
                'match_type': 'superlike' if like_type == 'superlike' or mutual.data[0].get('like_type') == 'superlike' else 'like',
                'matched_at': datetime.utcnow().isoformat()
            }
            match_result = self.db('matches').insert(match_data).execute()
            return {'status': 'match', 'match': match_result.data[0] if match_result.data else None}
        
        return {'status': 'liked', 'like': like_result.data[0] if like_result.data else None}
    
    def get_user_matches(self, user_id: str) -> List[Dict]:
        """Get user matches"""
        result = self.db('matches').select('*, user1:users!matches_user1_id_fkey(*), user2:users!matches_user2_id_fkey(*)')\
            .or_(f'user1_id.eq.{user_id},user2_id.eq.{user_id}')\
            .eq('status', 'active')\
            .order('matched_at', desc=True)\
            .execute()
        return result.data if result.data else []
    
    def create_block(self, user_id: str, blocked_user_id: str) -> Optional[Dict]:
        """Create a block"""
        block_data = {
            'user_id': user_id,
            'blocked_user_id': blocked_user_id,
            'created_at': datetime.utcnow().isoformat()
        }
        result = self.db('blocks').insert(block_data).execute()
        return result.data[0] if result.data else None
    
    # ========== REFERRAL METHODS ==========
    
    def generate_referral_code(self, name: str) -> str:
        """Generate unique referral code"""
        import random
        import string
        base = name.replace(" ", "").lower()[:10]
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
        return f"{base}_{random_suffix}"
    
    def process_referral(self, referral_code: str, new_user_id: str) -> Optional[Dict]:
        """Process referral when new user registers"""
        # Find referrer
        referrer = self.db('users').select('id').eq('referral_code', referral_code).execute()
        if referrer.data:
            referral_data = {
                'referrer_id': referrer.data[0]['id'],
                'referred_id': new_user_id,
                'referral_code': referral_code,
                'status': 'registered',
                'created_at': datetime.utcnow().isoformat()
            }
            result = self.db('referrals').insert(referral_data).execute()
            
            # Increment referrer count
            self.db('users').update({
                'total_referrals': self.db('users').select('total_referrals').eq('id', referrer.data[0]['id']).execute().data[0]['total_referrals'] + 1
            }).eq('id', referrer.data[0]['id']).execute()
            
            return result.data[0] if result.data else None
        return None
    
    def mark_referral_paid(self, referred_user_id: str) -> None:
        """Mark referral as paid when referred user pays"""
        referral = self.db('referrals').select('*').eq('referred_id', referred_user_id).execute()
        if referral.data:
            self.db('referrals').update({
                'status': 'paid',
                'paid_at': datetime.utcnow().isoformat()
            }).eq('id', referral.data[0]['id']).execute()
            
            # Check if referrer qualifies for free subscription
            referrer_id = referral.data[0]['referrer_id']
            paid_count = self.db('referrals').select('*', count='exact')\
                .eq('referrer_id', referrer_id)\
                .eq('status', 'paid')\
                .execute()
            
            if paid_count.count >= 5:
                # Grant free subscription
                expiry = datetime.utcnow() + timedelta(days=Settings.PAYMENT_DURATION_DAYS)
                self.db('users').update({
                    'subscription_active': True,
                    'subscription_start': datetime.utcnow().isoformat(),
                    'subscription_end': expiry.isoformat()
                }).eq('id', referrer_id).execute()
    
    # ========== STATISTICS ==========
    
    def get_dashboard_stats(self) -> Dict:
        """Get admin dashboard statistics"""
        stats = {}
        
        # User stats
        users_query = self.db('users').select('*', count='exact').execute()
        stats['total_users'] = users_query.count
        
        active = self.db('users').select('*', count='exact').eq('status', 'active').execute()
        stats['active_users'] = active.count
        
        pending = self.db('users').select('*', count='exact').eq('status', 'pending').execute()
        stats['pending_users'] = pending.count
        
        # Payment stats
        payments = self.db('payments').select('amount').eq('status', 'approved').execute()
        stats['total_revenue'] = sum(p['amount'] for p in payments.data) if payments.data else 0
        
        pending_payments = self.db('payments').select('*', count='exact').eq('status', 'pending').execute()
        stats['pending_payments'] = pending_payments.count
        
        # Today's stats
        today = datetime.utcnow().date().isoformat()
        new_today = self.db('users').select('*', count='exact')\
            .gte('created_at', today).execute()
        stats['new_users_today'] = new_today.count
        
        # Match stats
        matches = self.db('matches').select('*', count='exact').execute()
        stats['total_matches'] = matches.count
        
        likes = self.db('likes').select('*', count='exact').execute()
        stats['total_likes'] = likes.count
        
        # Photo stats
        photos = self.db('photos').select('*', count='exact').execute()
        stats['total_photos'] = photos.count
        
        pending_photos = self.db('photos').select('*', count='exact').eq('is_approved', False).execute()
        stats['pending_photos'] = pending_photos.count
        
        # Referral stats
        referrals = self.db('referrals').select('*', count='exact').execute()
        stats['total_referrals'] = referrals.count
        
        return stats

# Singleton instance
supabase = SupabaseClient()