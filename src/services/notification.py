"""
Notification service for Habesha Dating Bot
"""
import logging
import asyncio
from typing import List, Dict, Optional
from datetime import datetime

from src.config.settings import Settings
from src.database.supabase_client import supabase

logger = logging.getLogger(__name__)

class NotificationService:
    """Handle push notifications and alerts"""
    
    def __init__(self):
        self.bot = None
        logger.info("✅ Notification service initialized")
    
    def set_bot(self, bot):
        """Set bot instance for sending messages"""
        self.bot = bot
    
    async def send_notification(self, user_id: int, text: str, parse_mode: str = 'Markdown') -> bool:
        """Send notification to a user"""
        if not self.bot:
            logger.error("Bot not set in notification service")
            return False
        
        try:
            await self.bot.send_message(
                chat_id=user_id,
                text=text,
                parse_mode=parse_mode
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send notification to {user_id}: {e}")
            return False
    
    async def broadcast_to_admins(self, text: str, parse_mode: str = 'Markdown'):
        """Send notification to all admins"""
        if not self.bot:
            return
        
        for admin_id in Settings.ADMIN_IDS:
            try:
                await self.bot.send_message(
                    chat_id=admin_id,
                    text=text,
                    parse_mode=parse_mode
                )
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id}: {e}")
    
    async def notify_new_match(self, user1_id: int, user2_id: int, user1_name: str, user2_name: str):
        """Notify both users about a new match"""
        if not self.bot:
            return
        
        # Notify user 1
        text1 = f"🎉 *It's a Match!*\n\nYou matched with {user2_name}! 💕"
        await self.send_notification(user1_id, text1)
        
        # Notify user 2
        text2 = f"🎉 *It's a Match!*\n\nYou matched with {user1_name}! 💕"
        await self.send_notification(user2_id, text2)
        
        logger.info(f"Match notification sent to {user1_id} and {user2_id}")
    
    async def notify_payment_approved(self, user_id: int, expiry_date: str):
        """Notify user that payment was approved"""
        text = f"""
✅ *Payment Approved!*

Your subscription is now active until {expiry_date}.

Start browsing with /browse
        """
        await self.send_notification(user_id, text)
    
    async def notify_profile_approved(self, user_id: int):
        """Notify user that profile was approved"""
        text = """
✅ *Profile Approved!*

Your profile has been verified and approved.

Next steps:
1. Use /subscribe to activate
2. Upload payment receipt
3. Start browsing with /browse
        """
        await self.send_notification(user_id, text)
    
    async def send_weekly_reminder(self, user_id: int, likes_left: int):
        """Send weekly reminder about remaining likes"""
        text = f"""
📅 *Weekly Reminder*

You have {likes_left} likes remaining this week.

Use /browse to find matches!
        """
        await self.send_notification(user_id, text)
    
    async def send_expiry_reminder(self, user_id: int, days_left: int):
        """Send subscription expiry reminder"""
        if days_left <= 0:
            text = """
⚠️ *Subscription Expired*

Your subscription has expired. 
Use /subscribe to renew and continue matching!
            """
        else:
            text = f"""
⚠️ *Subscription Expiring Soon*

Your subscription will expire in {days_left} days.

Use /subscribe to renew and avoid interruption!
            """
        await self.send_notification(user_id, text)
    
    async def send_announcement(self, user_ids: List[int], text: str) -> Dict[str, int]:
        """Send announcement to multiple users"""
        stats = {'sent': 0, 'failed': 0}
        
        for user_id in user_ids:
            success = await self.send_notification(user_id, f"📢 *Announcement*\n\n{text}")
            if success:
                stats['sent'] += 1
            else:
                stats['failed'] += 1
            await asyncio.sleep(0.05)  # Rate limiting
        
        return stats
    
    async def get_active_users_for_announcement(self, target: str = 'all') -> List[int]:
        """Get user IDs for announcement based on target"""
        query = supabase.db('users').select('telegram_id')
        
        if target == 'active':
            query = query.eq('status', 'active').eq('subscription_active', True)
        elif target == 'pending':
            query = query.eq('status', 'pending')
        elif target == 'paid':
            query = query.eq('payment_status', 'paid')
        
        result = query.execute()
        return [u['telegram_id'] for u in result.data] if result.data else []

# Singleton instance
notification_service = NotificationService()