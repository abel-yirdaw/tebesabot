"""
Referral handler for Habesha Dating Bot
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

from src.database.supabase_client import supabase
from src.config.settings import Settings

logger = logging.getLogger(__name__)

class ReferralHandler:
    """Handle referral program"""
    
    def __init__(self, db):
        self.db = db
    
    async def show_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show referral program information"""
        user = self.db.get_user(update.effective_user.id)
        
        if not user:
            await update.message.reply_text("Please register first with /start")
            return
        
        lang = user.get('language', 'en')
        
        # Generate referral link
        bot_username = (await context.bot.get_me()).username
        referral_link = f"https://t.me/{bot_username}?start={user.get('referral_code', '')}"
        
        # Get referral stats
        referrals = self.db.client.table('referrals')\
            .select('*')\
            .eq('referrer_id', user['id'])\
            .execute()
        
        paid_count = sum(1 for r in referrals.data if r['status'] == 'paid')
        
        if lang == 'am':
            text = f"""
🤝 *የማጣቀሻ ፕሮግራም*

የእርስዎ ማጣቀሻ አገናኝ:
`{referral_link}`

*እንዴት እንደሚሰራ:*
1. አገናኝዎን ለጓደኞችዎ ያጋሩ
2. ሲመዘገቡ እና ሲከፍሉ ክሬዲት ያገኛሉ
3. 5 ክፍያ ካገኙ በኋላ ነፃ ደንበኝነት ያገኛሉ!

*የእርስዎ ስታቲስቲክስ:*
• ጠቅላላ ማጣቀሻ: {len(referrals.data)}
• የተከፈለ: {paid_count}
• የቀረ: {5 - paid_count} / 5
            """
        else:
            text = f"""
🤝 *Referral Program*

Your referral link:
`{referral_link}`

*How it works:*
1. Share your link with friends
2. When they register and pay, you get credit
3. Get 3 months FREE after 5 paid referrals!

*Your Stats:*
• Total referrals: {len(referrals.data)}
• Paid referrals: {paid_count}
• Progress: {paid_count}/5
            """
        
        keyboard = [[
            InlineKeyboardButton("📤 Share Link", switch_inline_query=referral_link),
            InlineKeyboardButton("👥 My Referrals", callback_data='my_referrals')
        ]]
        
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard),
            disable_web_page_preview=True
        )
    
    async def my_referrals(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user's referrals"""
        query = update.callback_query
        await query.answer()
        
        user = self.db.get_user(update.effective_user.id)
        
        if not user:
            await query.edit_message_text("Please register first.")
            return
        
        referrals = self.db.client.table('referrals')\
            .select('*, referred:referred_id(*)')\
            .eq('referrer_id', user['id'])\
            .execute()
        
        if not referrals.data:
            await query.edit_message_text(
                "You haven't referred anyone yet. Share your referral link to start earning!"
            )
            return
        
        text = "👥 *Your Referrals:*\n\n"
        for ref in referrals.data[:10]:
            referred = ref.get('referred', {})
            status_emoji = "✅" if ref['status'] == 'paid' else "⏳"
            name = referred.get('full_name', 'Unknown')
            date = ref['created_at'][:10] if ref.get('created_at') else ''
            text += f"{status_emoji} {name} - {ref['status']} ({date})\n"
        
        if len(referrals.data) > 10:
            text += f"\n... and {len(referrals.data) - 10} more"
        
        await query.edit_message_text(text, parse_mode='Markdown')