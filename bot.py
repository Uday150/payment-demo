from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import razorpay
import logging

# Logging
logging.basicConfig(level=logging.INFO)

# Store users waiting for payment
pending_users = {}

# Razorpay keys
RAZORPAY_KEY = "rzp_live_SRnNlwWsYU6Mw9"
RAZORPAY_SECRET = "7FudgDrjr4oEpcyjLPhaTSO6"

client_razor = razorpay.Client(auth=(RAZORPAY_KEY, RAZORPAY_SECRET))

# Google Sheets setup
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

sheet = client.open("Gate buyers").sheet1

# Telegram bot token
TOKEN = "8624598326:AAF2tanpbyfSKroRX7BPSN5q8b7lzhek8Lk"

# Razorpay payment link
PAYMENT_LINK = "https://rzp.io/rzp/MLUVHCa"


# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text(
            "Welcome to GATE 2026 Study Logs 📚\n\n"
            "Send your email to continue."
        )


# Handle email input
async def handle_email(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message:
        return

    email = update.message.text
    user_id = update.message.from_user.id

    pending_users[user_id] = email

    await update.message.reply_text(
        "✅ Email received!\n\n"
        "Pay ₹68 using the link below:\n"
        f"{PAYMENT_LINK}\n\n"
        "After payment send:\n"
        "/verify PAYMENT_ID"
    )


# Verify payment
async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message:
        return

    user_id = update.message.from_user.id

    if user_id not in pending_users:
        await update.message.reply_text("❌ Send email first.")
        return

    args = context.args

    if len(args) == 0:
        await update.message.reply_text(
            "Send like:\n/verify pay_xxxxxxxxx"
        )
        return

    payment_id = args[0]

    if not payment_id.startswith("pay_"):
        payment_id = "pay_" + payment_id

    try:

        payment = client_razor.payment.fetch(payment_id)

        if payment["status"] == "captured" and payment["amount"] == 6800:

            email = pending_users[user_id]
            username = update.message.from_user.username or "NoUsername"
            time = datetime.now().strftime("%d-%m-%Y %H:%M")

            try:
                sheet.append_row([email, username, payment_id, time])
            except Exception as sheet_error:
                logging.error(f"Sheet error: {sheet_error}")

            await update.message.reply_text(
                "✅ Payment Verified!\n\n"
                "Join GATE Study Logs group:\n"
                "https://t.me/+8XmC_-3-bsM3YWY1\n\n"
                "You will get a Clockify invite email within 24 hours."
            )

            del pending_users[user_id]

        else:
            await update.message.reply_text("❌ Payment not completed.")

    except Exception as e:
        logging.error(e)
        await update.message.reply_text("❌ Invalid payment ID.")


# Build bot
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("verify", verify))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_email))

print("BOT STARTED")

# Run bot
app.run_polling()