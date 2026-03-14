from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
import logging
from typing import Dict, List
import json

from database.supabase_client import supabase
from config.settings import Settings
from utils.analytics import Analytics

logger = logging.getLogger(__name__)

class AdminHandler:
    """Enhanced admin panel with comprehensive features"""
    
    def __init__(self):
        self.analytics = Analytics()
    
    async def panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Main admin dashboard"""
        if not Settings.is_admin(update.effective_user.id):
            await update.message.reply_text("⛔ Unauthorized access.")
            return
        
        # Get real-time stats
        stats = supabase.get_dashboard_stats()
        
        dashboard = f"""
👨‍💼 *Admin Dashboard*
━━━━━━━━━━━━━━━━━━━━━━━
📊 *System Status*
• Total Users: {stats['total_users']}
• Active: {stats['active_users']}
• Pending: {stats['pending_users']}
• New Today: {stats['new_users_today']}

💰 *Revenue*
• Total: {stats['total_revenue']} Birr
• Pending Payments: {stats['pending_payments']}

💕 *Activity*
• Matches: {stats['total_matches']}
• Likes: {stats['total_likes']}

🕒 {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
        """
        
        keyboard = [
            [InlineKeyboardButton("👥 Pending Approvals", callback_data='admin_pending')],
            [InlineKeyboardButton("💰 Payment Queue", callback_data='admin_payments')],
            [InlineKeyboardButton("📸 Photo Verification", callback_data='admin_photos')],
            [InlineKeyboardButton("📊 Analytics", callback_data='admin_analytics')],
            [InlineKeyboardButton("📢 Announcements", callback_data='admin_announce')],
            [InlineKeyboardButton("🔍 User Search", callback_data='admin_search')],
            [InlineKeyboardButton("⚙️ Settings", callback_data='admin_settings')],
            [InlineKeyboardButton("📈 Reports", callback_data='admin_reports')]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(dashboard, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all admin callbacks"""
        query = update.callback_query
        await query.answer()
        
        if not Settings.is_admin(update.effective_user.id):
            await query.edit_message_text("⛔ Unauthorized")
            return
        
        data = query.data
        
        if data == 'admin_pending':
            await self.show_pending_users(update, context)
        elif data == 'admin_payments':
            await self.show_pending_payments(update, context)
        elif data == 'admin_photos':
            await self.show_photo_verifications(update, context)
        elif data == 'admin_analytics':
            await self.show_analytics(update, context)
        elif data == 'admin_announce':
            await self.start_announcement(update, context)
        elif data == 'admin_search':
            await self.start_user_search(update, context)
        elif data == 'admin_settings':
            await self.show_settings(update, context)
        elif data == 'admin_reports':
            await self.show_reports(update, context)
        elif data.startswith('approve_user_'):
            await self.approve_user(update, context)
        elif data.startswith('reject_user_'):
            await self.reject_user(update, context)
        elif data.startswith('approve_payment_'):
            await self.approve_payment(update, context)
        elif data.startswith('reject_payment_'):
            await self.reject_payment(update, context)
        elif data.startswith('verify_photo_'):
            await self.verify_photo(update, context)
        elif data.startswith('user_details_'):
            await self.show_user_details(update, context)
    
    async def show_pending_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show pending users with quick actions"""
        users = supabase.db('users').select('*').eq('status', 'pending').execute()
        
        if not users.data:
            await update.callback_query.edit_message_text("✅ No pending users")
            return
        
        for user in users.data[:5]:  # Show 5 at a time
            # Get user photos
            photos = supabase.db('photos').select('*').eq('user_id', user['id']).execute()
            
            card = f"""
🆔 *User:* {user['full_name']}
📱 @{user['username'] or 'N/A'}
📅 Registered: {user['created_at'][:10]}
📍 {user['location']}, {user['region']}
📸 Photos: {len(photos.data)}/5
🔍 AI Score: {user.get('ai_verification_score', 'N/A')}
            """
            
            keyboard = [
                [
                    InlineKeyboardButton("✅ Approve", callback_data=f"approve_user_{user['id']}"),
                    InlineKeyboardButton("❌ Reject", callback_data=f"reject_user_{user['id']}")
                ],
                [InlineKeyboardButton("👤 View Details", callback_data=f"user_details_{user['id']}")]
            ]
            
            # Send first photo if exists
            if photos.data:
                await context.bot.send_photo(
                    chat_id=update.effective_user.id,
                    photo=photos.data[0]['photo_url'],
                    caption=card,
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                await context.bot.send_message(
                    chat_id=update.effective_user.id,
                    text=card,
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
    
    async def approve_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Approve user with automated welcome"""
        query = update.callback_query
        user_id = query.data.split('_')[2]
        
        # Update user status
        supabase.db('users').update({
            'status': 'active',
            'approved_at': datetime.utcnow().isoformat(),
            'approved_by': update.effective_user.id
        }).eq('id', user_id).execute()
        
        # Get user details
        user = supabase.db('users').select('*').eq('id', user_id).execute().data[0]
        
        # Send welcome message
        welcome_msg = f"""
✅ *Welcome to Habesha Dating Bot!*

Your profile has been approved by our admins.

Next steps:
1. Use /subscribe to activate your account
2. Upload payment receipt
3. Start browsing with /browse

We wish you the best in finding your match! 🎉
        """
        
        await context.bot.send_message(
            chat_id=user['telegram_id'],
            text=welcome_msg,
            parse_mode='Markdown'
        )
        
        # Log activity
        supabase.db('activity_log').insert({
            'user_id': user_id,
            'action': 'user_approved',
            'metadata': {'admin_id': update.effective_user.id}
        }).execute()
        
        await query.edit_message_caption(
            caption=f"✅ User {user['full_name']} approved successfully!"
        )
    
    async def show_pending_payments(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show payment queue with verification tools"""
        payments = supabase.db('payments').select('*, users(*)').eq('status', 'pending').execute()
        
        if not payments.data:
            await update.callback_query.edit_message_text("💰 No pending payments")
            return
        
        for payment in payments.data[:5]:
            user = payment['users']
            
            card = f"""
💰 *Payment #{payment['id'][:8]}*
👤 {user['full_name']} (@{user['username']})
💵 Amount: {payment['amount']} Birr
📅 {payment['created_at'][:16]}
📱 Status: Pending Verification
            """
            
            keyboard = [
                [
                    InlineKeyboardButton("✅ Approve", callback_data=f"approve_payment_{payment['id']}"),
                    InlineKeyboardButton("❌ Reject", callback_data=f"reject_payment_{payment['id']}")
                ]
            ]
            
            await context.bot.send_photo(
                chat_id=update.effective_user.id,
                photo=payment['receipt_url'],
                caption=card,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    
    async def approve_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Approve payment and activate subscription"""
        query = update.callback_query
        payment_id = query.data.split('_')[2]
        
        # Process payment
        user_id = supabase.approve_payment(payment_id, update.effective_user.id)
        
        if user_id:
            await query.edit_message_caption(
                caption="✅ Payment approved! Subscription activated."
            )
            
            # Send notification
            await context.bot.send_message(
                chat_id=user_id,
                text="✅ *Payment Verified!*\n\nYour subscription is now active. Start browsing with /browse!",
                parse_mode='Markdown'
            )
    
    async def show_analytics(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show detailed analytics with charts"""
        stats = self.analytics.get_detailed_stats(days=30)
        
        report = f"""
📊 *Analytics Report*

*User Growth (30 days)*
• New users: {stats['growth']['new_users']}
• Growth rate: {stats['growth']['rate']}%
• Active users: {stats['active_users']}

*Engagement*
• Daily active: {stats['engagement']['daily_active']}
• Weekly active: {stats['engagement']['weekly_active']}
• Monthly active: {stats['engagement']['monthly_active']}
• Avg. session: {stats['engagement']['avg_session_min']} min

*Matching*
• Total matches: {stats['matching']['total']}
• Avg. matches/user: {stats['matching']['avg_per_user']}
• Like conversion: {stats['matching']['conversion_rate']}%

*Revenue*
• Total: {stats['revenue']['total']} Birr
• Monthly: {stats['revenue']['monthly']} Birr
• Avg. per user: {stats['revenue']['avg_per_user']} Birr

*Top Locations*
{self._format_top_locations(stats['locations'])}

*Peak Hours*
• Most active: {stats['peak_hours']['peak_time']} UTC
• Activity score: {stats['peak_hours']['score']}
        """
        
        keyboard = [
            [InlineKeyboardButton("📥 Export CSV", callback_data='export_csv')],
            [InlineKeyboardButton("🔙 Back", callback_data='admin_back')]
        ]
        
        await update.callback_query.edit_message_text(
            report,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def start_announcement(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start announcement creation with scheduling"""
        keyboard = [
            [InlineKeyboardButton("📢 All Users", callback_data='announce_all')],
            [InlineKeyboardButton("✅ Active Users", callback_data='announce_active')],
            [InlineKeyboardButton("⏳ Pending Users", callback_data='announce_pending')],
            [InlineKeyboardButton("💰 Paid Users", callback_data='announce_paid')],
            [InlineKeyboardButton("📍 By Location", callback_data='announce_location')]
        ]
        
        await update.callback_query.edit_message_text(
            "Select announcement target:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        context.user_data['announcement_mode'] = True
    
    async def send_announcement(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send announcement to selected users"""
        if not context.user_data.get('announcement_mode'):
            return
        
        text = update.message.text
        target = context.user_data.get('announce_target', 'all')
        
        # Get target users
        query = supabase.db('users').select('telegram_id')
        if target == 'active':
            query = query.eq('status', 'active').eq('subscription_active', True)
        elif target == 'pending':
            query = query.eq('status', 'pending')
        elif target == 'paid':
            query = query.eq('payment_status', 'paid')
        
        users = query.execute()
        
        # Send to each user
        success = 0
        failed = 0
        
        for user in users.data:
            try:
                await context.bot.send_message(
                    chat_id=user['telegram_id'],
                    text=f"📢 *Announcement*\n\n{text}",
                    parse_mode='Markdown'
                )
                success += 1
            except:
                failed += 1
        
        await update.message.reply_text(
            f"✅ Announcement sent!\n"
            f"✓ Success: {success}\n"
            f"✗ Failed: {failed}"
        )
        
        context.user_data['announcement_mode'] = False
    
    async def show_user_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show detailed user profile for admin"""
        query = update.callback_query
        user_id = query.data.split('_')[2]
        
        # Get user data
        user = supabase.db('users').select('*').eq('id', user_id).execute().data[0]
        photos = supabase.db('photos').select('*').eq('user_id', user_id).execute().data
        payments = supabase.db('payments').select('*').eq('user_id', user_id).execute().data
        matches = supabase.db('matches').select('*')\
            .or_(f'user1_id.eq.{user_id},user2_id.eq.{user_id}')\
            .execute().data
        
        details = f"""
👤 *User Details*
━━━━━━━━━━━━━━━━━━━━━━━
ID: {user['id'][:8]}...
Telegram: @{user['username'] or 'N/A'}
Name: {user['full_name']}
Age: {user['age']}
Gender: {user['gender']}
Location: {user['location']}, {user['region']}
Religion: {user['religion'] or 'N/A'}
Occupation: {user['occupation']}

📊 *Activity*
Joined: {user['created_at'][:10]}
Status: {user['status']}
Subscription: {'✅ Active' if user.get('subscription_active') else '❌ Inactive'}
Likes left: {user['weekly_likes']}/5
Matches: {len(matches)}
Photos: {len(photos)}/5
Payments: {len(payments)}

💬 *Bio*
{user['bio'] or 'No bio'}
        """
        
        # Show photos
        if photos:
            await context.bot.send_media_group(
                chat_id=update.effective_user.id,
                media=[InputMediaPhoto(p['photo_url']) for p in photos[:5]]
            )
        
        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text=details,
            parse_mode='Markdown'
        )
    
    def _format_top_locations(self, locations: List[Dict]) -> str:
        """Format top locations for display"""
        if not locations:
            return "No data"
        
        formatted = []
        for loc in locations[:5]:
            formatted.append(f"• {loc['region']}: {loc['count']} users")
        
        return "\n".join(formatted)