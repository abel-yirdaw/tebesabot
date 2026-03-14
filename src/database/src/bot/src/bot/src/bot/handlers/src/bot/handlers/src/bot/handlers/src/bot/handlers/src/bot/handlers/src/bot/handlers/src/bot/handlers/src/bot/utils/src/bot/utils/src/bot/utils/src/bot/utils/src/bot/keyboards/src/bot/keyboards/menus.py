"""
Keyboard layouts for Habesha Dating Bot
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from src.bot.utils.helpers import get_text

def main_menu_keyboard(lang='en'):
    """Main menu keyboard"""
    keyboard = [
        [InlineKeyboardButton(get_text('browse', lang), callback_data='menu_browse')],
        [InlineKeyboardButton(get_text('my_matches', lang), callback_data='menu_matches')],
        [InlineKeyboardButton(get_text('my_profile', lang), callback_data='menu_profile')],
        [InlineKeyboardButton(get_text('subscribe', lang), callback_data='menu_subscribe')],
        [InlineKeyboardButton(get_text('referral', lang), callback_data='menu_referral')],
        [InlineKeyboardButton(get_text('language', lang), callback_data='menu_language')],
        [InlineKeyboardButton(get_text('help', lang), callback_data='menu_help')]
    ]
    return InlineKeyboardMarkup(keyboard)

def language_keyboard():
    """Language selection keyboard"""
    keyboard = [
        [InlineKeyboardButton("English", callback_data='lang_en_new')],
        [InlineKeyboardButton("አማርኛ", callback_data='lang_am_new')]
    ]
    return InlineKeyboardMarkup(keyboard)

def gender_keyboard(lang='en'):
    """Gender selection keyboard"""
    keyboard = [
        [InlineKeyboardButton(get_text('male', lang), callback_data='gender_male')],
        [InlineKeyboardButton(get_text('female', lang), callback_data='gender_female')]
    ]
    return InlineKeyboardMarkup(keyboard)

def ethnicity_keyboard(lang='en'):
    """Ethnicity selection keyboard"""
    keyboard = [
        [InlineKeyboardButton(get_text('ethnicity_amhara', lang), callback_data='ethnicity_amhara')],
        [InlineKeyboardButton(get_text('ethnicity_oromo', lang), callback_data='ethnicity_oromo')],
        [InlineKeyboardButton(get_text('ethnicity_tigray', lang), callback_data='ethnicity_tigray')],
        [InlineKeyboardButton("ሌላ / Other", callback_data='ethnicity_other')]
    ]
    return InlineKeyboardMarkup(keyboard)

def religion_keyboard(lang='en'):
    """Religion selection keyboard"""
    keyboard = [
        [InlineKeyboardButton(get_text('religion_orthodox', lang), callback_data='religion_orthodox')],
        [InlineKeyboardButton(get_text('religion_muslim', lang), callback_data='religion_muslim')],
        [InlineKeyboardButton(get_text('religion_protestant', lang), callback_data='religion_protestant')],
        [InlineKeyboardButton("ሌላ / Other", callback_data='religion_other')],
        [InlineKeyboardButton(get_text('skip', lang), callback_data='religion_skip')]
    ]
    return InlineKeyboardMarkup(keyboard)

def goal_keyboard(lang='en'):
    """Relationship goal selection keyboard"""
    keyboard = [
        [InlineKeyboardButton(get_text('goal_marriage', lang), callback_data='goal_marriage')],
        [InlineKeyboardButton(get_text('goal_dating', lang), callback_data='goal_dating')],
        [InlineKeyboardButton(get_text('goal_friendship', lang), callback_data='goal_friendship')],
        [InlineKeyboardButton(get_text('goal_notsure', lang), callback_data='goal_notsure')]
    ]
    return InlineKeyboardMarkup(keyboard)

def confirmation_keyboard(lang='en'):
    """Confirmation keyboard"""
    keyboard = [
        [
            InlineKeyboardButton(get_text('yes_submit', lang), callback_data='submit_registration'),
            InlineKeyboardButton(get_text('no_edit', lang), callback_data='edit_registration')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def admin_main_keyboard():
    """Admin main menu keyboard"""
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
    return InlineKeyboardMarkup(keyboard)

def back_button(callback_data='menu_back'):
    """Back button only"""
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data=callback_data)]])