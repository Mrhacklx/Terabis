import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from pymongo import MongoClient
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

# MongoDB Setup
client = MongoClient(os.getenv("MONGO_URI"))
db = client["telegram_bot_db"]
users_collection = db["users"]

# Telegram Bot Token
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Function to validate API Key
def validate_api_key(api_key):
    try:
        test_url = "https://example.com"  # Replace with a valid test URL
        api_url = f"https://bisgram.com/api?api={api_key}&url={test_url}"
        response = requests.get(api_url)
        data = response.json()
        return data.get("status") == "success"
    except Exception as e:
        logger.error(f"Error validating API key: {e}")
        return False

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    await update.message.reply_text(f"Hi {user.first_name}!\nWelcome to Terabis Bot.\n\nHow to connect: /help")

# /connect command
async def connect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    message_parts = update.message.text.split(" ")

    if len(message_parts) < 2:
        await update.message.reply_text("Please provide your API key. Example: /connect YOUR_API_KEY")
        return

    api_key = message_parts[1]

    if validate_api_key(api_key):
        users_collection.update_one(
            {"telegram_id": user_id},
            {"$set": {"api_key": api_key}},
            upsert=True,
        )
        await update.message.reply_text("✅ API key connected successfully! You can now shorten links.")
    else:
        await update.message.reply_text("❌ Invalid API key. Please try again.")

# /disconnect command
async def disconnect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    result = users_collection.delete_one({"telegram_id": user_id})

    if result.deleted_count > 0:
        await update.message.reply_text("✅ Your API key has been disconnected successfully.")
    else:
        await update.message.reply_text("⚠️ No API key is connected.")

# /view command
async def view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user = users_collection.find_one({"telegram_id": user_id})

    if user and "api_key" in user:
        await update.message.reply_text(f"✅ Your connected API key: `{user['api_key']}`", parse_mode="Markdown")
    else:
        await update.message.reply_text("⚠️ No API key is connected. Use /connect to link one.")

# /help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "How to Connect:\n"
        "1. Go to [Bisgram.com](https://bisgram.com)\n"
        "2. Create an Account\n"
        "3. Navigate to Tools > Developer API\n"
        "4. Copy the API token\n"
        "5. Use the command: /connect YOUR_API_KEY\n"
        "   Example: /connect 123456789abcdef\n\n"
        "For assistance, contact [Support Bot](https://t.me/ayushx2026_bot)"
    )
    await update.message.reply_text(help_text, parse_mode="MarkdownV2")

# Fallback for invalid messages
async def handle_invalid_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚠️ Please use a valid command. Use /help for assistance.")

# Main function to run the bot
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Register commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("connect", connect))
    application.add_handler(CommandHandler("disconnect", disconnect))
    application.add_handler(CommandHandler("view", view))
    application.add_handler(CommandHandler("help", help_command))

    # Handle invalid messages
    application.add_handler(MessageHandler(filters.ALL, handle_invalid_messages))

    # Run the bot
    logger.info("Bot started.")
    application.run_polling()

if __name__ == "__main__":
    main()
