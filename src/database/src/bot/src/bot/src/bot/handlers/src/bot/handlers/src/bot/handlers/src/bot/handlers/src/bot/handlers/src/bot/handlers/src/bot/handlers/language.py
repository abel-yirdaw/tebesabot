"""
Language handler for Habesha Dating Bot
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import logging

from src.database.supabase_client import supabase
from src.bot.utils.helpers import get_text, LANGUAGES

logger = logging.getLogger(__name__)

class LanguageHandler:
    """Handle language selection and switching"""
    
    def __init__(self, db):
        self.db = db
    
    async def show_language_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show language selection menu"""
        user = self.db.get_user(update.effective_user.id)
        current_lang = user.get('language', 'en') if user else 'en'
        
        keyboard = []
        for code, name in LANGUAGES.items():
            display = f"✅ {name}" if code == current_lang else name
            callback = f"lang_{code}_menu"
            keyboard.append([InlineKeyboardButton(display, callback_data=callback)])
        
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data='menu_back')])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(
                "🌐 *Select your language* / *ቋንቋዎን ይምረጡ*",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                "🌐 *Select your language* / *ቋንቋዎን ይምረጡ*",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
    
    async def handle_language_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle language selection callback"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        parts = data.split('_')
        lang_code = parts[1]
        source = parts[2] if len(parts) > 2 else 'menu'
        
        user = self.db.get_user(update.effective_user.id)
        
        if user:
            # Update existing user's language
            self.db.update_user(update.effective_user.id, language=lang_code)
            
            # Confirm change
            if lang_code == 'am':
                await query.edit_message_text("✅ ቋንቋ ወደ አማርኛ ተቀይሯል")
            else:
                await query.edit_message_text("✅ Language changed to English")
            
            # Show main menu if from menu
            if source == 'menu':
                from src.bot.keyboards.menus import main_menu_keyboard
                await query.message.reply_text(
                    "🏠 *Main Menu*",
                    parse_mode='Markdown',
                    reply_markup=main_menu_keyboard(lang_code)
                )
        else:
            # New user - store in context
            context.user_data['language'] = lang_code
            context.user_data['registration_phase'] = 'name'
            
            await query.edit_message_text(
                get_text('welcome', lang_code),
                parse_mode='Markdown'
            )
            return 'NAME'
    
    async def get_user_language(self, telegram_id: int) -> str:
        """Get user's language preference"""
        user = self.db.get_user(telegram_id)
        return user.get('language', 'en') if user else 'en'