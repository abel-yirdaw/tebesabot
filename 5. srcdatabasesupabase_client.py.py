from supabase import create_client, Client
from config.settings import Settings
import logging
from typing import Optional, Dict, Any
from datetime import datetime
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
    
    def execute_sql(self, query: str, params: Dict = None):
        """Execute raw SQL (admin only)"""
        return self.client.rpc('execute_sql', {'query': query, 'params': params}).execute()
    
    # User methods
    def create_user(self, user_data: Dict[str, Any]) -> Dict:
        """Create new user"""
        user_data['created_at'] = datetime.utcnow().isoformat()
        user_data['status'] = 'pending'
        user_data['weekly_likes'] = Settings.WEEKLY_LIKES
        
        result = self.db('users').insert(user_data).execute()
        return result.data[0] if result.data else None
    
    def get_user(self, telegram_id: int) -> Optional[Dict]:
        """Get user by telegram ID"""
        result = self.db('users').select('*').eq('telegram_id', telegram_id).execute()
        return result.data[0] if result.data else None
    
    def update_user(self, telegram_id: int, **kwargs) -> Optional[Dict]:
        """Update user"""
        kwargs['updated_at'] = datetime.utcnow().isoformat()
        result = self.db('users').update(kwargs).eq('telegram_id', telegram_id).execute()
        return result.data[0] if result.data else None
    
    # Photo methods
    def add_photo(self, user_id: int, photo_url: str, is_selfie: bool = True) -> Dict:
        """Add photo for verification"""
        photo_data = {
            'user_id': user_id,
            'photo_url': photo_url,
            'is_selfie': is_selfie,
            'uploaded_at': datetime.utcnow().isoformat(),
            'verified': False
        }
        result = self.db('photos').insert(photo_data).execute()
        return result.data[0] if result.data else None
    
    def verify_photo(self, photo_id: int, admin_id: int, approved: bool, reason: str = None):
        """Verify photo"""
        update_data = {
            'verified': approved,
            'verified_by': admin_id,
            'verified_at': datetime.utcnow().isoformat(),
            'rejection_reason': reason
        }
        return self.db('photos').update(update_data).eq('id', photo_id).execute()
    
    # Payment methods
    def create_payment(self, user_id: int, receipt_url: str) -> Dict:
        """Create payment record"""
        payment_data = {
            'user_id': user_id,
            'receipt_url': receipt_url,
            'amount': Settings.PAYMENT_AMOUNT,
            'status': 'pending',
            'created_at': datetime.utcnow().isoformat()
        }
        result = self.db('payments').insert(payment_data).execute()
        return result.data[0] if result.data else None
    
    def approve_payment(self, payment_id: int, admin_id: int):
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
            expiry = datetime.utcnow().replace(hour=23, minute=59, second=59)
            expiry = expiry.replace(day=expiry.day + Settings.PAYMENT_DURATION_DAYS)
            
            self.db('users').update({
                'subscription_active': True,
                'subscription_expiry': expiry.isoformat(),
                'status': 'active',
                'payment_status': 'paid'
            }).eq('id', user_id).execute()
            
            return user_id
        return None
    
    # Matching methods
    def get_potential_matches(self, user_id: int, gender: str, limit: int = 10) -> List[Dict]:
        """Get potential matches using Supabase RPC"""
        result = self.client.rpc('get_potential_matches', {
            'p_user_id': user_id,
            'p_gender': gender,
            'p_limit': limit
        }).execute()
        return result.data if result.data else []
    
    def create_like(self, from_user: int, to_user: int, like_type: str = 'like') -> Dict:
        """Create a like and check for match"""
        # Insert like
        like_data = {
            'from_user_id': from_user,
            'to_user_id': to_user,
            'like_type': like_type,
            'created_at': datetime.utcnow().isoformat()
        }
        like_result = self.db('likes').insert(like_data).execute()
        
        # Check for mutual like
        mutual = self.db('likes').select('*')\
            .eq('from_user_id', to_user)\
            .eq('to_user_id', from_user)\
            .execute()
        
        if mutual.data:
            # Create match
            match_data = {
                'user1_id': min(from_user, to_user),
                'user2_id': max(from_user, to_user),
                'matched_at': datetime.utcnow().isoformat()
            }
            match_result = self.db('matches').insert(match_data).execute()
            return {'status': 'match', 'match': match_result.data[0]}
        
        return {'status': 'liked', 'like': like_result.data[0]}
    
    # Referral methods
    def process_referral(self, referral_code: str, new_user_id: int):
        """Process referral when new user registers"""
        # Find referrer
        referrer = self.db('users').select('id').eq('referral_code', referral_code).execute()
        if referrer.data:
            referral_data = {
                'referrer_id': referrer.data[0]['id'],
                'referred_id': new_user_id,
                'status': 'registered',
                'created_at': datetime.utcnow().isoformat()
            }
            self.db('referrals').insert(referral_data).execute()
            
            # Increment referrer count
            self.db('users').update({
                'total_referrals': self.db('users').select('total_referrals').eq('id', referrer.data[0]['id']).execute().data[0]['total_referrals'] + 1
            }).eq('id', referrer.data[0]['id']).execute()
    
    # Analytics
    def get_dashboard_stats(self) -> Dict:
        """Get admin dashboard statistics"""
        stats = {}
        
        # User stats
        stats['total_users'] = self.db('users').select('count', count='exact').execute().count
        stats['active_users'] = self.db('users').select('count', count='exact').eq('status', 'active').execute().count
        stats['pending_users'] = self.db('users').select('count', count='exact').eq('status', 'pending').execute().count
        
        # Payment stats
        stats['total_revenue'] = self.db('payments').select('amount').eq('status', 'approved').execute()
        stats['pending_payments'] = self.db('payments').select('count', count='exact').eq('status', 'pending').execute().count
        
        # Today's stats
        today = datetime.utcnow().date().isoformat()
        stats['new_users_today'] = self.db('users').select('count', count='exact')\
            .gte('created_at', today).execute().count
        
        return stats

# Singleton instance
supabase = SupabaseClient()