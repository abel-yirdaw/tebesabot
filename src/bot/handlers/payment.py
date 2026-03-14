"""
Payment handler for Habesha Dating Bot
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime
import logging

from src.database.supabase_client import supabase
from src.config.settings import Settings
from src.services.storage import storage_service
from src.bot.utils.helpers import get_text

logger = logging.getLogger(__name__)

class PaymentHandler:
    """Handle payments and subscriptions"""
    
    def __init__(self, db, config):
        self.db = db
        self.config = config
    
    async def start_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start payment process"""
        user = self.db.get_user(update.effective_user.id)
        
        if not user:
            await update.message.reply_text("Please register first with /start")
            return
        
        lang = user.get('language', 'en')
        
        if user.get('subscription_active'):
            expiry = user.get('subscription_end', '')
            if expiry:
                expiry_date = expiry[:10]
                await update.message.reply_text(
                    f"✅ You already have an active subscription until {expiry_date}!"
                )
            else:
                await update.message.reply_text("✅ You already have an active subscription!")
            return
        
        payment_text = f"""
💰 *Subscription Payment*

To activate your account, pay {Settings.PAYMENT_AMOUNT} Birr for {Settings.PAYMENT_DURATION_DAYS} days access.

*Payment Methods:*

1️⃣ **TeleBirr**
   📱 Number: +251911234567
   📝 Name: Habesha Dating SC

2️⃣ **CBE Birr**
   🏦 Account: 1000134567890
   📝 Name: Habesha Dating SC

3️⃣ **Bank Transfer**
   🏦 Bank: Commercial Bank of Ethiopia
   💳 Account: 1000134567890
   📝 Name: Habesha Dating SC

*After payment:*
1. Take a clear screenshot of the receipt
2. Click the button below and upload
3. Admin will verify within 24 hours

*Note:* Receipt must show:
- Transaction date
- Amount ({Settings.PAYMENT_AMOUNT} Birr)
- Reference number
        """
        
        keyboard = [[InlineKeyboardButton("📤 Upload Receipt", callback_data='upload_receipt')]]
        
        await update.message.reply_text(
            payment_text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def handle_receipt_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle receipt upload callback"""
        query = update.callback_query
        await query.answer()
        
        context.user_data['payment_phase'] = 'upload_receipt'
        
        await query.edit_message_text(
            "📤 Please upload your payment receipt as a photo.\n\n"
            "Make sure the receipt is clear and shows all transaction details."
        )
    
    async def handle_receipt(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process uploaded receipt"""
        user = self.db.get_user(update.effective_user.id)
        
        if not user:
            await update.message.reply_text("Please register first with /start")
            return
        
        # Get the photo
        photo = update.message.photo[-1]
        photo_file = await photo.get_file()
        
        # Download photo
        file_bytes = await photo_file.download_as_bytearray()
        
        # Show processing message
        processing_msg = await update.message.reply_text("🔄 Processing receipt...")
        
        # Upload to Supabase storage
        receipt_url = await storage_service.upload_receipt(
            user_id=user['id'],
            file_bytes=bytes(file_bytes),
            filename=f"receipt_{datetime.utcnow().timestamp()}.jpg"
        )
        
        if not receipt_url:
            await processing_msg.edit_text("❌ Failed to upload receipt. Please try again.")
            return
        
        # Create payment record
        payment = self.db.create_payment(user['id'], receipt_url)
        
        if payment:
            await processing_msg.edit_text(
                "✅ Receipt uploaded successfully! Admin will verify within 24 hours.\n\n"
                "You'll be notified once your payment is approved."
            )
            
            # Notify admin channel
            await self.notify_admin(update, context, user, payment)
        else:
            await processing_msg.edit_text("❌ Failed to create payment record. Please try again.")
        
        context.user_data.pop('payment_phase', None)
    
    async def notify_admin(self, update, context, user, payment):
        """Notify admin about new payment"""
        message = f"""
💰 *New Payment Received*

👤 *User:* {user['full_name']} (@{user['username']})
💵 *Amount:* {payment['amount']} Birr
📅 *Date:* {payment['created_at'][:16]}
🆔 *Payment ID:* {payment['id'][:8]}

Please verify the receipt.
        """
        
        keyboard = [[
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_payment_{payment['id']}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_payment_{payment['id']}")
        ]]
        
        await context.bot.send_photo(
            chat_id=Settings.ADMIN_CHANNEL_ID,
            photo=payment['receipt_url'],
            caption=message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def check_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check payment/subscription status"""
        user = self.db.get_user(update.effective_user.id)
        
        if not user:
            await update.message.reply_text("Please register first with /start")
            return
        
        if user.get('subscription_active'):
            expiry = user.get('subscription_end', '')
            if expiry:
                expiry_date = expiry[:10]
                await update.message.reply_text(
                    f"✅ *Subscription Active*\n\n"
                    f"Valid until: {expiry_date}\n"
                    f"Days left: {(datetime.fromisoformat(expiry) - datetime.utcnow()).days}",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text("✅ Subscription Active")
        else:
            # Check for pending payment
            payments = self.db.client.table('payments')\
                .select('*')\
                .eq('user_id', user['id'])\
                .eq('status', 'pending')\
                .execute()
            
            if payments.data:
                await update.message.reply_text(
                    f"⏳ *Payment Pending*\n\n"
                    f"Submitted: {payments.data[0]['created_at'][:16]}\n"
                    f"Please wait for admin verification.",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    "❌ *No Active Subscription*\n\n"
                    "Use /subscribe to activate.",
                    parse_mode='Markdown'
                )