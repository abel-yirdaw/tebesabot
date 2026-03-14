"""
Main bot class for Habesha Dating Bot
"""
import logging
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ConversationHandler, filters
)
from telegram import BotCommand
import asyncio

from src.config.settings import Settings
from src.database.supabase_client import supabase
from src.bot.handlers import (
    RegistrationHandler, MatchingHandler, PaymentHandler,
    AdminHandler, ReferralHandler, LanguageHandler,
    # Registration states
    NAME, AGE, GENDER, LOCATION, REGION, ETHNICITY, ETHNICITY_TEXT,
    RELIGION, RELIGION_TEXT, CHURCH, EDUCATION, OCCUPATION,
    GOAL, BIO, PHOTOS, REFERRAL, CONFIRM
)

logger = logging.getLogger(__name__)

class HabeshaDatingBot:
    """Main bot class"""
    
    def __init__(self):
        self.config = Settings()
        self.config.validate()
        
        self.db = supabase
        self.application = Application.builder().token(self.config.BOT_TOKEN).build()
        
        # Initialize handlers
        self.registration = RegistrationHandler(self.db)
        self.matching = MatchingHandler(self.db)
        self.payment = PaymentHandler(self.db, self.config)
        self.admin = AdminHandler(self.db, self.config)
        self.referral = ReferralHandler(self.db)
        self.language = LanguageHandler(self.db)
        
        logger.info("✅ Bot initialized")
    
    def setup_handlers(self):
        """Set up all handlers"""
        
        # Registration conversation handler
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.registration.start)],
            states={
                'LANGUAGE': [CallbackQueryHandler(self.language.handle_language_selection)],
                NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.registration.handle_input)],
                AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.registration.handle_input)],
                GENDER: [CallbackQueryHandler(self.registration.handle_callback)],
                LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.registration.handle_input)],
                REGION: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.registration.handle_input)],
                ETHNICITY: [CallbackQueryHandler(self.registration.handle_callback)],
                ETHNICITY_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.registration.handle_input)],
                RELIGION: [CallbackQueryHandler(self.registration.handle_callback)],
                RELIGION_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.registration.handle_input)],
                CHURCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.registration.handle_input)],
                EDUCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.registration.handle_input)],
                OCCUPATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.registration.handle_input)],
                GOAL: [CallbackQueryHandler(self.registration.handle_callback)],
                BIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.registration.handle_input)],
                PHOTOS: [MessageHandler(filters.PHOTO, self.registration.handle_photos)],
                REFERRAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.registration.handle_input)],
                CONFIRM: [CallbackQueryHandler(self.registration.handle_callback)],
            },
            fallbacks=[CommandHandler('cancel', self.registration.cancel)],
        )
        self.application.add_handler(conv_handler)
        
        # Basic commands
        self.application.add_handler(CommandHandler("profile", self.registration.view_profile))
        self.application.add_handler(CommandHandler("browse", self.matching.browse))
        self.application.add_handler(CommandHandler("matches", self.matching.view_matches))
        self.application.add_handler(CommandHandler("subscribe", self.payment.start_payment))
        self.application.add_handler(CommandHandler("referral", self.referral.show_info))
        self.application.add_handler(CommandHandler("language", self.language.show_language_menu))
        self.application.add_handler(CommandHandler("lang", self.language.show_language_menu))
        self.application.add_handler(CommandHandler("help", self.help_command))
        
        # Admin commands
        self.application.add_handler(CommandHandler("admin", self.admin.panel))
        self.application.add_handler(CommandHandler("stats", self.admin.show_stats_command))
        self.application.add_handler(CommandHandler("announce", self.admin.start_announcement_command))
        self.application.add_handler(CommandHandler("search", self.admin.search_user_command))
        
        # Callback query handler
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Photo handlers (for receipts)
        self.application.add_handler(MessageHandler(
            filters.PHOTO & filters.ChatType.PRIVATE, 
            self.handle_photo
        ))
        
        logger.info("✅ Handlers setup complete")
    
    async def handle_callback(self, update, context):
        """Handle all callback queries"""
        query = update.callback_query
        data = query.data
        
        # Route to appropriate handler
        if data.startswith('lang_'):
            await self.language.handle_language_selection(update, context)
        elif data.startswith('menu_'):
            await self.handle_menu(update, context)
        elif data.startswith('like_') or data.startswith('superlike_'):
            await self.matching.handle_like(update, context)
        elif data.startswith('block_'):
            await self.matching.handle_block(update, context)
        elif data in ['next_profile', 'prev_profile', 'continue_browsing']:
            await self.matching.handle_navigation(update, context)
        elif data.startswith('approve_user_') or data.startswith('reject_user_') or \
             data.startswith('approve_payment_') or data.startswith('reject_payment_') or \
             data.startswith('approve_photo_') or data.startswith('reject_photo_') or \
             data.startswith('user_details_') or data == 'admin_pending' or \
             data == 'admin_payments' or data == 'admin_photos' or \
             data == 'admin_analytics' or data == 'admin_announce' or \
             data == 'admin_search' or data == 'admin_settings' or \
             data == 'admin_reports' or data == 'admin_back':
            await self.admin.handle_callback(update, context)
        elif data == 'upload_receipt':
            await self.payment.handle_receipt_upload(update, context)
        elif data == 'my_referrals':
            await self.referral.my_referrals(update, context)
    
    async def handle_menu(self, update, context):
        """Handle menu selections"""
        query = update.callback_query
        action = query.data.replace('menu_', '')
        
        if action == 'browse':
            await self.matching.browse(update, context)
        elif action == 'matches':
            await self.matching.view_matches(update, context)
        elif action == 'profile':
            await self.registration.view_profile(update, context)
        elif action == 'subscribe':
            await self.payment.start_payment(update, context)
        elif action == 'referral':
            await self.referral.show_info(update, context)
        elif action == 'language':
            await self.language.show_language_menu(update, context)
        elif action == 'help':
            await self.help_command(update, context)
    
    async def handle_photo(self, update, context):
        """Handle photo uploads"""
        user = self.db.get_user(update.effective_user.id)
        
        if not user:
            await update.message.reply_text("Please start the bot with /start first.")
            return
        
        if context.user_data.get('payment_phase') == 'upload_receipt':
            await self.payment.handle_receipt(update, context)
        elif context.user_data.get('registration_phase') == 'photos':
            # This should be handled by the conversation handler
            pass
        else:
            await update.message.reply_text("You can upload photos during registration or payment.")
    
    async def help_command(self, update, context):
        """Send help message"""
        user = self.db.get_user(update.effective_user.id)
        
        if user and user.language == 'am':
            help_text = """
🤵 *የሐበሻ የትዳር ቦት - እገዛ*

*ትዕዛዞች:*
/start - ይመዝገቡ
/profile - መገለጫዎን ይመልከቱ
/browse - አጋሮችን ይፈልጉ
/matches - ተዛማጆችዎን ይመልከቱ
/subscribe - ይመዝገቡ (100 ብር)
/referral - የማጣቀሻ ፕሮግራም
/language - ቋንቋ ይቀይሩ
/help - እገዛ

*አስተዳዳሪ ትዕዛዞች*
/admin - የአስተዳዳሪ ፓነል
/stats - ስታቲስቲክስ
/announce - ማስታወቂያ ይላኩ
            """
        else:
            help_text = """
🤵 *Habesha Dating Bot - Help*

*Commands:*
/start - Register
/profile - View profile
/browse - Find matches
/matches - Your matches
/subscribe - Subscribe (100 Birr)
/referral - Referral program
/language - Change language
/help - Show this help

*Admin Commands*
/admin - Admin panel
/stats - View statistics
/announce - Send announcement
            """
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def post_init(self, application):
        """Setup after initialization"""
        commands = [
            BotCommand("start", "Start the bot"),
            BotCommand("profile", "View profile"),
            BotCommand("browse", "Find matches"),
            BotCommand("matches", "Your matches"),
            BotCommand("subscribe", "Subscribe"),
            BotCommand("referral", "Referral program"),
            BotCommand("language", "Change language"),
            BotCommand("help", "Get help")
        ]
        await application.bot.set_my_commands(commands)
        logger.info("✅ Bot commands set")
    
    async def run(self):
        """Run the bot"""
        self.setup_handlers()
        self.application.post_init = self.post_init
        
        logger.info("🚀 Bot starting...")
        
        if self.config.ENV == 'development':
            # Polling mode for development
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            logger.info("✅ Bot started in polling mode")
            
            # Keep running
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                logger.info("👋 Shutting down...")
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
        else:
            # Webhook mode for production
            await self.application.run_webhook(
                listen="0.0.0.0",
                port=8000,
                url_path=self.config.BOT_TOKEN,
                webhook_url=f"{self.config.WEBHOOK_URL}/{self.config.BOT_TOKEN}"
            )