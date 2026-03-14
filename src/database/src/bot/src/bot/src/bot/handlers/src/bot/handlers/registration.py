"""
Registration handler for Habesha Dating Bot
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from datetime import datetime
import logging

from src.database.supabase_client import supabase
from src.bot.utils.helpers import get_text, validate_age
from src.bot.keyboards.menus import (
    gender_keyboard, ethnicity_keyboard, religion_keyboard,
    goal_keyboard, confirmation_keyboard, language_keyboard
)

# Registration states
(NAME, AGE, GENDER, LOCATION, REGION, ETHNICITY, ETHNICITY_TEXT,
 RELIGION, RELIGION_TEXT, CHURCH, EDUCATION, OCCUPATION,
 GOAL, BIO, PHOTOS, REFERRAL, CONFIRM) = range(17)

logger = logging.getLogger(__name__)

class RegistrationHandler:
    """Handle user registration"""
    
    def __init__(self, db):
        self.db = db
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start registration"""
        user = update.effective_user
        existing_user = self.db.get_user(user.id)
        
        if existing_user:
            if existing_user['status'] == 'pending':
                await update.message.reply_text(
                    "Your profile is under review. You'll be notified when approved. 🙏"
                )
            elif existing_user['status'] == 'active':
                await self.show_main_menu(update, context, existing_user)
            else:
                await update.message.reply_text(
                    "Please contact support for assistance."
                )
            return ConversationHandler.END
        
        # New user - show language selection
        await update.message.reply_text(
            "🌐 *Select your language* / *ቋንቋዎን ይምረጡ*",
            parse_mode='Markdown',
            reply_markup=language_keyboard()
        )
        return 'LANGUAGE'
    
    async def handle_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text input during registration"""
        phase = context.user_data.get('registration_phase')
        text = update.message.text
        lang = context.user_data.get('language', 'en')
        
        if phase == 'name':
            context.user_data['name'] = text
            await update.message.reply_text(get_text('age_prompt', lang))
            context.user_data['registration_phase'] = 'age'
            return AGE
            
        elif phase == 'age':
            if text.isdigit() and 18 <= int(text) <= 100:
                context.user_data['age'] = int(text)
                await update.message.reply_text(
                    get_text('gender_prompt', lang),
                    reply_markup=gender_keyboard(lang)
                )
                return GENDER
            else:
                await update.message.reply_text(get_text('invalid_age', lang))
                return AGE
        
        elif phase == 'location':
            context.user_data['location'] = text
            await update.message.reply_text(get_text('region_prompt', lang))
            context.user_data['registration_phase'] = 'region'
            return REGION
        
        elif phase == 'region':
            context.user_data['region'] = text
            await update.message.reply_text(
                get_text('ethnicity_prompt', lang),
                reply_markup=ethnicity_keyboard(lang)
            )
            return ETHNICITY
        
        elif phase == 'ethnicity_text':
            context.user_data['ethnicity'] = text
            await update.message.reply_text(
                get_text('religion_prompt', lang),
                reply_markup=religion_keyboard(lang)
            )
            return RELIGION
        
        elif phase == 'religion_text':
            context.user_data['religion'] = text
            await update.message.reply_text(get_text('church_prompt', lang))
            context.user_data['registration_phase'] = 'church'
            return CHURCH
        
        elif phase == 'church':
            if text.lower() != 'skip':
                context.user_data['church'] = text
            await update.message.reply_text(get_text('education_prompt', lang))
            context.user_data['registration_phase'] = 'education'
            return EDUCATION
        
        elif phase == 'education':
            context.user_data['education'] = text
            await update.message.reply_text(get_text('occupation_prompt', lang))
            context.user_data['registration_phase'] = 'occupation'
            return OCCUPATION
        
        elif phase == 'occupation':
            context.user_data['occupation'] = text
            await update.message.reply_text(
                get_text('goal_prompt', lang),
                reply_markup=goal_keyboard(lang)
            )
            return GOAL
        
        elif phase == 'bio':
            if len(text) <= 500:
                context.user_data['bio'] = text
                await update.message.reply_text(get_text('photo_prompt', lang))
                context.user_data['registration_phase'] = 'photos'
                context.user_data['photos'] = []
                return PHOTOS
            else:
                await update.message.reply_text(get_text('bio_too_long', lang))
                return BIO
        
        elif phase == 'referral':
            if text.lower() != 'skip':
                context.user_data['referral_code'] = text
            await self.show_summary(update, context)
            return CONFIRM
        
        return ConversationHandler.END
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        lang = context.user_data.get('language', 'en')
        
        if data.startswith('gender_'):
            gender = data.split('_')[1]
            context.user_data['gender'] = gender
            context.user_data['looking_for'] = 'female' if gender == 'male' else 'male'
            await query.edit_message_text(get_text('location_prompt', lang))
            context.user_data['registration_phase'] = 'location'
            return LOCATION
        
        elif data.startswith('ethnicity_'):
            ethnicity = data.split('_')[1]
            if ethnicity == 'other':
                await query.edit_message_text("Please type your ethnicity:")
                context.user_data['registration_phase'] = 'ethnicity_text'
                return ETHNICITY
            else:
                context.user_data['ethnicity'] = ethnicity
                await query.edit_message_text(
                    get_text('religion_prompt', lang),
                    reply_markup=religion_keyboard(lang)
                )
                return RELIGION
        
        elif data.startswith('religion_'):
            if data == 'religion_skip':
                context.user_data['religion'] = None
                await query.edit_message_text(get_text('church_prompt', lang))
                context.user_data['registration_phase'] = 'church'
                return CHURCH
            elif data == 'religion_other':
                await query.edit_message_text("Please type your religion:")
                context.user_data['registration_phase'] = 'religion_text'
                return RELIGION
            else:
                religion = data.split('_')[1]
                context.user_data['religion'] = religion
                await query.edit_message_text(get_text('church_prompt', lang))
                context.user_data['registration_phase'] = 'church'
                return CHURCH
        
        elif data.startswith('goal_'):
            goal_map = {
                'marriage': get_text('goal_marriage', lang),
                'dating': get_text('goal_dating', lang),
                'friendship': get_text('goal_friendship', lang),
                'notsure': get_text('goal_notsure', lang)
            }
            goal_key = data.split('_')[1]
            context.user_data['goal'] = goal_map[goal_key]
            await query.edit_message_text(get_text('bio_prompt', lang))
            context.user_data['registration_phase'] = 'bio'
            return BIO
        
        elif data == 'submit_registration':
            await self.submit_registration(update, context)
            return ConversationHandler.END
        elif data == 'edit_registration':
            await query.edit_message_text(get_text('welcome', lang))
            context.user_data['registration_phase'] = 'name'
            return NAME
        
        return ConversationHandler.END
    
    async def handle_photos(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle photo uploads"""
        photos = context.user_data.get('photos', [])
        lang = context.user_data.get('language', 'en')
        
        # Get the photo file
        photo = update.message.photo[-1]
        photo_file = await photo.get_file()
        
        # Store file_id (actual upload to Supabase happens at submission)
        photos.append({
            'file_id': photo_file.file_id,
            'file_size': photo.file_size
        })
        context.user_data['photos'] = photos
        
        if len(photos) < 3:
            remaining = 3 - len(photos)
            await update.message.reply_text(
                f"📸 Photo {len(photos)}/5. {remaining} more needed."
            )
        elif len(photos) >= 3 and len(photos) < 5:
            await update.message.reply_text(
                f"📸 Photo {len(photos)}/5. Send more or type /done"
            )
        elif len(photos) >= 5:
            await update.message.reply_text(get_text('referral_prompt', lang))
            context.user_data['registration_phase'] = 'referral'
            return REFERRAL
        
        return PHOTOS
    
    async def show_summary(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show registration summary"""
        data = context.user_data
        lang = data.get('language', 'en')
        
        gender_display = get_text('male', lang) if data.get('gender') == 'male' else get_text('female', lang)
        
        summary = f"""
📝 *Profile Summary*

*Name:* {data.get('name')}
*Age:* {data.get('age')}
*Gender:* {gender_display}
*Location:* {data.get('location')}, {data.get('region')}
*Ethnicity:* {data.get('ethnicity', 'Not specified')}
*Religion:* {data.get('religion', 'Not specified')}
*Education:* {data.get('education')}
*Occupation:* {data.get('occupation')}
*Goal:* {data.get('goal')}

*Bio:*
{data.get('bio')}

*Photos:* {len(data.get('photos', []))} uploaded

Is this correct?
        """
        
        await update.message.reply_text(
            summary,
            parse_mode='Markdown',
            reply_markup=confirmation_keyboard(lang)
        )
    
    async def submit_registration(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Submit registration"""
        query = update.callback_query
        user = update.effective_user
        data = context.user_data
        lang = data.get('language', 'en')
        
        # Create user in database
        db_user = self.db.create_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=data.get('name'),
            age=data.get('age'),
            gender=data.get('gender'),
            location=data.get('location'),
            region=data.get('region'),
            ethnicity=data.get('ethnicity'),
            religion=data.get('religion'),
            church=data.get('church'),
            education=data.get('education'),
            occupation=data.get('occupation'),
            relationship_goal=data.get('goal'),
            looking_for=data.get('looking_for'),
            bio=data.get('bio'),
            language=lang,
            status='pending'
        )
        
        if not db_user:
            await query.edit_message_text("❌ Registration failed. Please try again.")
            context.user_data.clear()
            return
        
        # Generate and save referral code
        referral_code = self.db.generate_referral_code(data.get('name', 'user'))
        self.db.update_user(user.id, referral_code=referral_code)
        
        # Process referral if provided
        if data.get('referral_code'):
            self.db.process_referral(data['referral_code'], db_user['id'])
        
        # Upload photos to Supabase storage
        from src.services.storage import storage_service
        
        photo_urls = []
        for i, photo in enumerate(data.get('photos', [])):
            # Download from Telegram
            file = await context.bot.get_file(photo['file_id'])
            file_bytes = await file.download_as_bytearray()
            
            # Upload to Supabase
            url = await storage_service.upload_profile_photo(
                user_id=db_user['id'],
                file_bytes=bytes(file_bytes),
                filename=f"photo_{i+1}.jpg"
            )
            if url:
                photo_urls.append(url)
                
                # Add to verification queue
                self.db.add_photo(
                    user_id=db_user['id'],
                    photo_url=url,
                    is_selfie=True
                )
        
        # Update user with photo URLs
        if photo_urls:
            self.db.update_user(user.id, profile_photos=photo_urls)
        
        await query.edit_message_text(
            get_text('registration_complete', lang),
            parse_mode='Markdown'
        )
        
        # Log activity
        self.db.client.table('activity_log').insert({
            'user_id': db_user['id'],
            'action': 'user_registered',
            'created_at': datetime.utcnow().isoformat()
        }).execute()
        
        # Notify admin channel
        await self.notify_admin(update, context, db_user, len(photo_urls))
        
        context.user_data.clear()
    
    async def notify_admin(self, update, context, user, photo_count):
        """Notify admin about new registration"""
        from src.config.settings import Settings
        
        message = f"""
🆕 *New Registration*

👤 *Name:* {user['full_name']}
📱 *Username:* @{user['username'] or 'N/A'}
📍 *Location:* {user['location']}, {user['region']}
📸 *Photos:* {photo_count}/5

Please review and approve/reject.
        """
        
        keyboard = [[
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_user_{user['id']}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_user_{user['id']}")
        ]]
        
        await context.bot.send_message(
            chat_id=Settings.ADMIN_CHANNEL_ID,
            text=message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def view_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """View user profile"""
        user = self.db.get_user(update.effective_user.id)
        
        if not user:
            await update.message.reply_text("Please register first with /start")
            return
        
        lang = user.get('language', 'en')
        
        status = "✅ Active" if user.get('subscription_active') else "❌ Inactive"
        days_left = 0
        if user.get('subscription_end'):
            expiry = datetime.fromisoformat(user['subscription_end'])
            days_left = (expiry - datetime.utcnow()).days
        
        text = f"""
👤 *Your Profile*

*Name:* {user['full_name']}
*Age:* {user['age']}
*Location:* {user['location']}, {user['region']}
*Religion:* {user.get('religion', 'Not specified')}
*Occupation:* {user.get('occupation', 'Not specified')}

*Subscription:* {status}
{'*Days left:* ' + str(days_left) if days_left > 0 else ''}
*Likes left:* {user.get('weekly_likes', 5)}/5

*Referral Code:* `{user.get('referral_code', 'N/A')}`
*Total Referrals:* {user.get('total_referrals', 0)}
        """
        
        # Get user photos
        photos = self.db.get_user_photos(user['id'])
        
        if photos:
            await context.bot.send_photo(
                chat_id=update.effective_user.id,
                photo=photos[0]['photo_url'],
                caption=text,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(text, parse_mode='Markdown')
    
    async def show_main_menu(self, update, context, user):
        """Show main menu"""
        from src.bot.keyboards.menus import main_menu_keyboard
        
        lang = user.get('language', 'en')
        
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.message.reply_text(
                "🏠 *Main Menu*",
                parse_mode='Markdown',
                reply_markup=main_menu_keyboard(lang)
            )
        else:
            await update.message.reply_text(
                "🏠 *Main Menu*",
                parse_mode='Markdown',
                reply_markup=main_menu_keyboard(lang)
            )
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel conversation"""
        await update.message.reply_text("Operation cancelled.")
        return ConversationHandler.END