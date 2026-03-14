"""
Matching handler for Habesha Dating Bot
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime
import logging

from src.database.supabase_client import supabase
from src.bot.utils.helpers import get_text

logger = logging.getLogger(__name__)

class MatchingHandler:
    """Handle matching functionality"""
    
    def __init__(self, db):
        self.db = db
    
    async def browse(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Browse profiles"""
        user = self.db.get_user(update.effective_user.id)
        
        if not user or user.get('status') != 'active':
            await update.message.reply_text("Please complete registration first.")
            return
        
        lang = user.get('language', 'en')
        
        if not user.get('subscription_active'):
            await update.message.reply_text(
                f"⚠️ Your subscription is not active.\nPlease use /subscribe to continue."
            )
            return
        
        if user.get('weekly_likes', 0) <= 0:
            await update.message.reply_text(
                "You've used all your 5 likes for this week. They'll reset next week."
            )
            return
        
        # Get potential matches
        candidates = self.db.get_potential_matches(user['id'], limit=10)
        
        if not candidates:
            await update.message.reply_text(
                "No potential matches found. Check back later!"
            )
            return
        
        context.user_data['candidates'] = [c['id'] for c in candidates]
        context.user_data['current_index'] = 0
        
        await self.show_profile(update, context, candidates[0])
    
    async def show_profile(self, update, context, candidate):
        """Show a profile"""
        user = self.db.get_user(update.effective_user.id)
        lang = user.get('language', 'en')
        
        profile_text = f"""
*{candidate['full_name']}, {candidate['age']}*
📍 {candidate['location']}, {candidate['region']}
🙏 {candidate.get('religion', 'N/A')}
💼 {candidate.get('occupation', 'N/A')}
🎓 {candidate.get('education', 'N/A')}

*About:*
{candidate.get('bio', 'No bio')}

✨ Compatibility: {candidate.get('compatibility_score', 0)}%
        """
        
        keyboard = [
            [
                InlineKeyboardButton("❤️ Like", callback_data=f"like_{candidate['id']}"),
                InlineKeyboardButton("⭐ Superlike", callback_data=f"superlike_{candidate['id']}")
            ],
            [
                InlineKeyboardButton("🚫 Block", callback_data=f"block_{candidate['id']}"),
                InlineKeyboardButton("⏭️ Next", callback_data='next_profile')
            ]
        ]
        
        # Add navigation
        candidates = context.user_data.get('candidates', [])
        current = context.user_data.get('current_index', 0)
        
        if len(candidates) > 1:
            nav_row = []
            if current > 0:
                nav_row.append(InlineKeyboardButton("◀️ Previous", callback_data='prev_profile'))
            if current < len(candidates) - 1:
                nav_row.append(InlineKeyboardButton("Next ▶️", callback_data='next_profile'))
            if nav_row:
                keyboard.insert(0, nav_row)
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Get profile photos
        photos = candidate.get('profile_photos', [])
        
        if photos and len(photos) > 0:
            # Handle both string and object formats
            if isinstance(photos[0], dict):
                photo_url = photos[0].get('url', photos[0])
            else:
                photo_url = photos[0]
                
            await context.bot.send_photo(
                chat_id=update.effective_user.id,
                photo=photo_url,
                caption=profile_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text=profile_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
    
    async def handle_like(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle like action"""
        query = update.callback_query
        user = self.db.get_user(update.effective_user.id)
        
        if not user:
            await query.edit_message_caption(caption="User not found")
            return
        
        lang = user.get('language', 'en')
        candidate_id = query.data.split('_')[1]
        like_type = query.data.split('_')[0]
        
        candidate = self.db.get_user_by_id(candidate_id)
        if not candidate:
            await query.edit_message_caption(caption="Profile not found")
            return
        
        if user.get('weekly_likes', 0) <= 0:
            await query.edit_message_caption(
                caption="No likes remaining!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Continue Browsing", callback_data='continue_browsing')
                ]])
            )
            return
        
        # Check superlike cost
        if like_type == 'superlike' and user.get('weekly_likes', 0) < 2:
            await query.edit_message_caption(
                caption="Superlike costs 2 likes! You don't have enough.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Continue Browsing", callback_data='continue_browsing')
                ]])
            )
            return
        
        # Create like
        result = self.db.create_like(user['id'], candidate_id, like_type)
        
        # Update likes count
        cost = 2 if like_type == 'superlike' else 1
        new_likes = user['weekly_likes'] - cost
        self.db.update_user(user['telegram_id'], weekly_likes=new_likes)
        
        if result['status'] == 'match':
            # It's a match!
            match = result.get('match')
            
            await query.edit_message_caption(
                caption=f"🎉 *It's a Match!* with {candidate['full_name']}!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💬 Send Message", callback_data=f"message_{candidate_id}")],
                    [InlineKeyboardButton("Continue Browsing", callback_data='continue_browsing')]
                ])
            )
            
            # Notify other user
            await context.bot.send_message(
                chat_id=candidate['telegram_id'],
                text=f"🎉 You matched with {user['full_name']}!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💬 Reply", callback_data=f"message_{user['id']}")]
                ])
            )
            
            # Log match
            self.db.client.table('activity_log').insert({
                'user_id': user['id'],
                'action': 'match_created',
                'metadata': {'matched_with': candidate_id}
            }).execute()
            
        else:
            await query.edit_message_caption(
                caption="✅ Like sent!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Continue Browsing", callback_data='continue_browsing')
                ]])
            )
    
    async def handle_block(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle block action"""
        query = update.callback_query
        user = self.db.get_user(update.effective_user.id)
        
        if not user:
            return
        
        blocked_id = query.data.split('_')[1]
        
        self.db.create_block(user['id'], blocked_id)
        
        await query.edit_message_caption(
            caption="🚫 User blocked",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Continue Browsing", callback_data='continue_browsing')
            ]])
        )
    
    async def view_matches(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """View user's matches"""
        user = self.db.get_user(update.effective_user.id)
        
        if not user:
            await update.message.reply_text("Please register first.")
            return
        
        matches = self.db.get_user_matches(user['id'])
        
        if not matches:
            await update.message.reply_text(
                "No matches yet. Use /browse to find people!"
            )
            return
        
        await update.message.reply_text(
            f"💕 *Your Matches* ({len(matches)})",
            parse_mode='Markdown'
        )
        
        for match in matches[:5]:
            # Determine other user
            other_id = match['user2_id'] if match['user1_id'] == user['id'] else match['user1_id']
            other = self.db.get_user_by_id(other_id)
            
            if not other:
                continue
            
            text = f"""
*{other['full_name']}, {other['age']}*
📍 {other['location']}, {other['region']}
Matched: {match['matched_at'][:10]}
            """
            
            keyboard = [[InlineKeyboardButton(
                "💬 Send Message", 
                callback_data=f"message_{other['id']}"
            )]]
            
            # Get profile photo
            photos = self.db.get_user_photos(other['id'])
            
            if photos:
                await context.bot.send_photo(
                    chat_id=user['telegram_id'],
                    photo=photos[0]['photo_url'],
                    caption=text,
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                await context.bot.send_message(
                    chat_id=user['telegram_id'],
                    text=text,
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
    
    async def handle_navigation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle profile navigation"""
        query = update.callback_query
        user = self.db.get_user(update.effective_user.id)
        
        if not user:
            return
        
        candidates = context.user_data.get('candidates', [])
        current = context.user_data.get('current_index', 0)
        
        if query.data == 'next_profile' and current < len(candidates) - 1:
            context.user_data['current_index'] = current + 1
            candidate = self.db.get_user_by_id(candidates[current + 1])
            await self.show_profile(update, context, candidate)
        elif query.data == 'prev_profile' and current > 0:
            context.user_data['current_index'] = current - 1
            candidate = self.db.get_user_by_id(candidates[current - 1])
            await self.show_profile(update, context, candidate)
        elif query.data == 'continue_browsing':
            # Delete the current message
            await query.message.delete()
            await self.browse(update, context)