"""
Admin handler for Habesha Dating Bot
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
import logging
from typing import Dict, List

from src.database.supabase_client import supabase
from src.config.settings import Settings
from src.bot.utils.helpers import get_text

logger = logging.getLogger(__name__)

class AdminHandler:
    """Enhanced admin panel with comprehensive features"""
    
    def __init__(self, db, config):
        self.db = db
        self.config = config
    
    async def panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Main admin dashboard"""
        if not Settings.is_admin(update.effective_user.id):
            await update.message.reply_text("⛔ Unauthorized access.")
            return
        
        # Get real-time stats
        stats = self.db.get_dashboard_stats()
        
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

📸 *Photos*
• Total: {stats['total_photos']}
• Pending: {stats['pending_photos']}

🤝 *Referrals*
• Total: {stats['total_referrals']}

🕒 {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
        """
        
        keyboard = [
            [InlineKeyboardButton("👥 Pending Users", callback_data='admin_pending')],
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
        elif data == 'admin_back':
            await self.panel(update, context)
        elif data.startswith('approve_user_'):
            await self.approve_user(update, context)
        elif data.startswith('reject_user_'):
            await self.reject_user(update, context)
        elif data.startswith('approve_payment_'):
            await self.approve_payment(update, context)
        elif data.startswith('reject_payment_'):
            await self.reject_payment(update, context)
        elif data.startswith('approve_photo_'):
            await self.approve_photo(update, context)
        elif data.startswith('reject_photo_'):
            await self.reject_photo(update, context)
        elif data.startswith('user_details_'):
            await self.show_user_details(update, context)
        elif data.startswith('announce_'):
            await self.set_announcement_target(update, context)
    
    async def show_pending_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show pending users with quick actions"""
        users = self.db.get_pending_users()
        
        if not users:
            await update.callback_query.edit_message_text("✅ No pending users")
            return
        
        await update.callback_query.edit_message_text(
            f"👥 *Pending Users* ({len(users)})\n\nSending profiles...",
            parse_mode='Markdown'
        )
        
        for user in users[:10]:  # Show 10 at a time
            # Get user photos
            photos = self.db.get_user_photos(user['id'], approved_only=False)
            
            card = f"""
🆔 *User:* {user['full_name']}
📱 @{user['username'] or 'N/A'}
📅 Registered: {user['created_at'][:10]}
📍 {user['location']}, {user['region']}
📸 Photos: {len(photos)}/5
🎂 Age: {user['age']}
🙏 Religion: {user.get('religion', 'N/A')}
💼 Occupation: {user.get('occupation', 'N/A')}
            """
            
            keyboard = [
                [
                    InlineKeyboardButton("✅ Approve", callback_data=f"approve_user_{user['id']}"),
                    InlineKeyboardButton("❌ Reject", callback_data=f"reject_user_{user['id']}")
                ],
                [InlineKeyboardButton("👤 View Details", callback_data=f"user_details_{user['id']}")]
            ]
            
            # Send first photo if exists
            if photos:
                await context.bot.send_photo(
                    chat_id=update.effective_user.id,
                    photo=photos[0]['photo_url'],
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
        user = self.db.approve_user(user_id, update.effective_user.id)
        
        if user:
            await query.edit_message_caption(
                caption=f"✅ User {user['full_name']} approved successfully!"
            )
            
            # Get user's language preference
            lang = user.get('language', 'en')
            
            # Send welcome message
            if lang == 'am':
                welcome_msg = f"""
✅ *እንኳን ደስ ያለዎት!*

መገለጫዎ ጸድቋል!

ቀጣይ እርምጃዎች:
1. ለመመዝገብ /subscribe ይጠቀሙ
2. የክፍያ ደረሰኝ ይላኩ
3. ማግኘት ለመጀመር /browse ይጠቀሙ

መልካም ምኞት! 🎉
                """
            else:
                welcome_msg = f"""
✅ *Congratulations!*

Your profile has been approved!

Next steps:
1. Use /subscribe to activate
2. Upload payment receipt
3. Start browsing with /browse

Best wishes! 🎉
                """
            
            await context.bot.send_message(
                chat_id=user['telegram_id'],
                text=welcome_msg,
                parse_mode='Markdown'
            )
            
            # Log activity
            self.db.client.table('activity_log').insert({
                'user_id': user_id,
                'action': 'user_approved',
                'metadata': {'admin_id': update.effective_user.id}
            }).execute()
    
    async def reject_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Reject user with reason"""
        query = update.callback_query
        user_id = query.data.split('_')[2]
        
        # Store in context to get reason
        context.user_data['rejecting_user'] = user_id
        
        await query.edit_message_caption(
            caption="Please enter the reason for rejection:"
        )
    
    async def show_pending_payments(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show payment queue with verification tools"""
        payments = self.db.get_pending_payments()
        
        if not payments:
            await update.callback_query.edit_message_text("💰 No pending payments")
            return
        
        await update.callback_query.edit_message_text(
            f"💰 *Pending Payments* ({len(payments)})\n\nSending receipts...",
            parse_mode='Markdown'
        )
        
        for payment in payments[:5]:
            user = payment.get('users', {})
            
            card = f"""
💰 *Payment #{payment['id'][:8]}*
👤 {user.get('full_name', 'Unknown')} (@{user.get('username', 'N/A')})
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
        user_id = self.db.approve_payment(payment_id, update.effective_user.id)
        
        if user_id:
            await query.edit_message_caption(
                caption="✅ Payment approved! Subscription activated."
            )
            
            # Get user details
            user = self.db.get_user_by_id(user_id)
            
            # Send notification
            expiry = user.get('subscription_end', '')
            if expiry:
                expiry_date = expiry[:10]
                
            await context.bot.send_message(
                chat_id=user['telegram_id'],
                text=f"✅ *Payment Verified!*\n\nYour subscription is now active until {expiry_date}. Start browsing with /browse!",
                parse_mode='Markdown'
            )
    
    async def reject_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Reject payment with reason"""
        query = update.callback_query
        payment_id = query.data.split('_')[2]
        
        context.user_data['rejecting_payment'] = payment_id
        
        await query.edit_message_caption(
            caption="Please enter the reason for rejection:"
        )
    
    async def show_photo_verifications(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show photos pending verification"""
        photos = self.db.get_pending_photos()
        
        if not photos:
            await update.callback_query.edit_message_text("📸 No pending photos")
            return
        
        await update.callback_query.edit_message_text(
            f"📸 *Pending Photos* ({len(photos)})\n\nSending photos...",
            parse_mode='Markdown'
        )
        
        for photo in photos[:10]:
            user = photo.get('users', {})
            
            card = f"""
📸 *Photo Verification*
👤 {user.get('full_name', 'Unknown')} (@{user.get('username', 'N/A')})
📅 Uploaded: {photo['uploaded_at'][:16]}
🤳 {'Selfie' if photo.get('is_selfie') else 'Photo'}
            """
            
            keyboard = [
                [
                    InlineKeyboardButton("✅ Approve", callback_data=f"approve_photo_{photo['id']}"),
                    InlineKeyboardButton("❌ Reject", callback_data=f"reject_photo_{photo['id']}")
                ]
            ]
            
            await context.bot.send_photo(
                chat_id=update.effective_user.id,
                photo=photo['photo_url'],
                caption=card,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    
    async def approve_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Approve photo"""
        query = update.callback_query
        photo_id = query.data.split('_')[2]
        
        photo = self.db.verify_photo(photo_id, update.effective_user.id, True)
        
        if photo:
            await query.edit_message_caption(
                caption="✅ Photo approved!"
            )
    
    async def reject_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Reject photo with reason"""
        query = update.callback_query
        photo_id = query.data.split('_')[2]
        
        context.user_data['rejecting_photo'] = photo_id
        
        await query.edit_message_caption(
            caption="Please enter the reason for rejection:"
        )
    
    async def show_analytics(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show detailed analytics"""
        stats = self.db.get_dashboard_stats()
        
        # Get additional stats
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        # User growth over time
        growth = self.db.client.table('users')\
            .select('created_at')\
            .gte('created_at', start_date.isoformat())\
            .execute()
        
        # Payment stats
        revenue_by_month = self.db.client.table('payments')\
            .select('amount, created_at')\
            .eq('status', 'approved')\
            .gte('created_at', start_date.isoformat())\
            .execute()
        
        report = f"""
📊 *Analytics Report*
━━━━━━━━━━━━━━━━━━━━━━━

*User Growth (30 days)*
• New users: {len(growth.data)}
• Growth rate: {round(len(growth.data)/30, 1)}/day
• Total users: {stats['total_users']}

*Engagement*
• Active users: {stats['active_users']}
• Conversion rate: {round(stats['active_users']/max(stats['total_users'],1)*100, 1)}%
• Pending: {stats['pending_users']}

*Matching*
• Total matches: {stats['total_matches']}
• Total likes: {stats['total_likes']}
• Avg matches/user: {round(stats['total_matches']/max(stats['active_users'],1), 1)}

*Revenue*
• Total: {stats['total_revenue']} Birr
• Monthly: {sum(p['amount'] for p in revenue_by_month.data)} Birr
• Avg per user: {round(stats['total_revenue']/max(stats['active_users'],1), 1)} Birr

*Photos*
• Total uploaded: {stats['total_photos']}
• Pending verification: {stats['pending_photos']}

*Referrals*
• Total: {stats['total_referrals']}
        """
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data='admin_back')]]
        
        await update.callback_query.edit_message_text(
            report,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def start_announcement(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start announcement creation"""
        keyboard = [
            [InlineKeyboardButton("📢 All Users", callback_data='announce_all')],
            [InlineKeyboardButton("✅ Active Users", callback_data='announce_active')],
            [InlineKeyboardButton("⏳ Pending Users", callback_data='announce_pending')],
            [InlineKeyboardButton("💰 Paid Users", callback_data='announce_paid')],
            [InlineKeyboardButton("📍 By Location", callback_data='announce_location')],
            [InlineKeyboardButton("🔙 Back", callback_data='admin_back')]
        ]
        
        await update.callback_query.edit_message_text(
            "📢 *Send Announcement*\n\nSelect target audience:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def set_announcement_target(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set announcement target and get message"""
        query = update.callback_query
        target = query.data.split('_')[1]
        
        context.user_data['announcement_target'] = target
        context.user_data['awaiting_announcement'] = True
        
        await query.edit_message_text(
            f"📝 Send the announcement message for *{target}* users:",
            parse_mode='Markdown'
        )
    
    async def start_user_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start user search"""
        await update.callback_query.edit_message_text(
            "🔍 Enter username or name to search:"
        )
        context.user_data['awaiting_search'] = True
    
    async def show_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show admin settings"""
        keyboard = [
            [InlineKeyboardButton("⚙️ Payment Amount", callback_data='settings_payment')],
            [InlineKeyboardButton("⏱️ Subscription Duration", callback_data='settings_duration')],
            [InlineKeyboardButton("❤️ Weekly Likes", callback_data='settings_likes')],
            [InlineKeyboardButton("🔙 Back", callback_data='admin_back')]
        ]
        
        await update.callback_query.edit_message_text(
            f"⚙️ *Settings*\n\n"
            f"Current:\n"
            f"• Payment: {Settings.PAYMENT_AMOUNT} Birr\n"
            f"• Duration: {Settings.PAYMENT_DURATION_DAYS} days\n"
            f"• Weekly Likes: {Settings.WEEKLY_LIKES}",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def show_reports(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show report options"""
        keyboard = [
            [InlineKeyboardButton("📊 User Report", callback_data='report_users')],
            [InlineKeyboardButton("💰 Revenue Report", callback_data='report_revenue')],
            [InlineKeyboardButton("💕 Match Report", callback_data='report_matches')],
            [InlineKeyboardButton("📥 Export All Data", callback_data='report_export')],
            [InlineKeyboardButton("🔙 Back", callback_data='admin_back')]
        ]
        
        await update.callback_query.edit_message_text(
            "📈 *Generate Reports*",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def show_user_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show detailed user profile for admin"""
        query = update.callback_query
        user_id = query.data.split('_')[2]
        
        # Get user data
        user = self.db.get_user_by_id(user_id)
        if not user:
            await query.edit_message_caption(caption="User not found")
            return
        
        photos = self.db.get_user_photos(user_id, approved_only=False)
        payments = self.db.client.table('payments').select('*').eq('user_id', user_id).execute()
        matches = self.db.get_user_matches(user_id)
        
        details = f"""
👤 *User Details*
━━━━━━━━━━━━━━━━━━━━━━━
ID: {user['id'][:8]}...
Telegram: @{user.get('username', 'N/A')}
Name: {user['full_name']}
Age: {user['age']}
Gender: {user['gender']}
Location: {user['location']}, {user['region']}
Religion: {user.get('religion', 'N/A')}
Occupation: {user.get('occupation', 'N/A')}

📊 *Activity*
Joined: {user['created_at'][:10]}
Status: {user['status']}
Subscription: {'✅ Active' if user.get('subscription_active') else '❌ Inactive'}
Likes left: {user.get('weekly_likes', 5)}/5
Matches: {len(matches)}
Photos: {len(photos)}/5
Payments: {len(payments.data)}

💬 *Bio*
{user.get('bio', 'No bio')}
        """
        
        # Show photos
        if photos:
            media = []
            for p in photos[:5]:
                from telegram import InputMediaPhoto
                media.append(InputMediaPhoto(p['photo_url']))
            
            if media:
                await context.bot.send_media_group(
                    chat_id=update.effective_user.id,
                    media=media
                )
        
        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text=details,
            parse_mode='Markdown'
        )
    
    async def show_stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        if not Settings.is_admin(update.effective_user.id):
            await update.message.reply_text("⛔ Unauthorized")
            return
        
        stats = self.db.get_dashboard_stats()
        
        report = f"""
📊 *Bot Statistics*

👥 Users: {stats['total_users']}
   Active: {stats['active_users']}
   Pending: {stats['pending_users']}
   New today: {stats['new_users_today']}

💰 Revenue: {stats['total_revenue']} Birr
   Pending payments: {stats['pending_payments']}

💕 Matches: {stats['total_matches']}
❤️ Likes: {stats['total_likes']}
        """
        
        await update.message.reply_text(report, parse_mode='Markdown')
    
    async def start_announcement_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /announce command"""
        if not Settings.is_admin(update.effective_user.id):
            await update.message.reply_text("⛔ Unauthorized")
            return
        
        context.user_data['awaiting_announcement'] = True
        await update.message.reply_text(
            "📢 Send the announcement message to all users:"
        )
    
    async def search_user_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /search command"""
        if not Settings.is_admin(update.effective_user.id):
            await update.message.reply_text("⛔ Unauthorized")
            return
        
        query = ' '.join(context.args) if context.args else ''
        if not query:
            await update.message.reply_text("Usage: /search [username or name]")
            return
        
        # Search users
        users = self.db.client.table('users')\
            .select('*')\
            .ilike('full_name', f'%{query}%')\
            .execute()
        
        if not users.data:
            await update.message.reply_text(f"No users found matching '{query}'")
            return
        
        for user in users.data[:5]:
            text = f"""
👤 {user['full_name']} (@{user.get('username', 'N/A')})
Status: {user['status']}
Subscription: {'✅' if user.get('subscription_active') else '❌'}
Joined: {user['created_at'][:10]}
            """
            await update.message.reply_text(text)