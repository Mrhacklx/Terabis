import json
import os
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils import executor
from aiohttp import web

# File to store user data (API keys)
user_data_file = "user_data.json"

# Load user data from file
if os.path.exists(user_data_file):
    with open(user_data_file, "r") as file:
        user_data = json.load(file)
else:
    user_data = {}

# Save user data to file
def save_user_data():
    with open(user_data_file, "w") as file:
        json.dump(user_data, file)

# Function to validate API Key
async def validate_api_key(api_key):
    try:
        test_url = "https://example.com"  # Replace with a valid URL for testing
        api_url = f"https://bisgram.com/api?api={api_key}&url={test_url}"
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                data = await response.json()
                return data.get("status") == "success"
    except Exception as e:
        print("Error validating API key:", e)
        return False

# Initialize bot and dispatcher
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 3000))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    await message.reply(
        f"Hi {message.from_user.first_name},\n\nWelcome to the Terabis \n\nHow to connect /help"
    )

@dp.message_handler(commands=['connect'])
async def connect_command(message: types.Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.reply("Please provide your API key. Example: /connect YOUR_API_KEY \n\nFor API ID /help")
        return

    api_key = parts[1]
    user_id = message.from_user.id

    if await validate_api_key(api_key):
        user_data[user_id] = {"apiKey": api_key}
        save_user_data()
        await message.reply("✅ API key connected successfully! You can now shorten links.")
    else:
        await message.reply("❌ Invalid API key. Please try again.\n\nHow to connect /help")

@dp.message_handler(commands=['disconnect'])
async def disconnect_command(message: types.Message):
    user_id = message.from_user.id

    if user_id in user_data:
        del user_data[user_id]
        save_user_data()
        await message.reply("✅ Your API key has been disconnected successfully.")
    else:
        await message.reply("⚠️ You have not connected an API key yet.")

@dp.message_handler(commands=['help'])
async def help_command(message: types.Message):
    await message.reply(
        """
How to Connect:
1. Go to [Bisgram.com](https://bisgram.com)
2. Create an Account
3. Click on the menu bar (top left side)
4. Click on *Tools > Developer API*
5. Copy the API token
6. Use this command: /connect YOUR_API_KEY
   Example: /connect 8268d7f25na2c690bk25d4k20fbc63p5p09d6906

For any confusion or help, contact [@ayushx2026_bot](https://t.me/ayushx2026_bot)
        """,
        parse_mode="MarkdownV2"
    )

@dp.message_handler(commands=['commands'])
async def commands_command(message: types.Message):
    await message.reply(
        """
🤖 *Link Shortener Bot Commands:*
- /connect [API_KEY] - Connect your API key.
- /disconnect - Disconnect your API key.
- /view - View your connected API key.
- /stats - View your link shortening stats.
- /help - How to connect to website.
        """,
        parse_mode="Markdown"
    )

@dp.message_handler(commands=['view'])
async def view_command(message: types.Message):
    user_id = message.from_user.id
    if user_id in user_data and "apiKey" in user_data[user_id]:
        await message.reply(f"✅ Your connected API key: `{user_data[user_id]['apiKey']}`", parse_mode="Markdown")
    else:
        await message.reply("⚠️ No API key is connected. Use /connect to link one.")

@dp.message_handler(commands=['stats'])
async def stats_command(message: types.Message):
    user_id = message.from_user.id
    link_count = user_data.get(user_id, {}).get("linkCount", 0)
    await message.reply(f"📊 You have shortened {link_count} links.")

@dp.message_handler()
async def handle_message(message: types.Message):
    user_id = message.from_user.id

    if user_id not in user_data or "apiKey" not in user_data[user_id]:
        await message.reply("⚠️ You haven't connected your API key yet. Please use /connect [API_KEY] to connect.")
        return

    api_key = user_data[user_id]["apiKey"]
    links = [word for word in message.text.split() if word.startswith("http")]

    if not links:
        await message.reply("Please send a valid link to shorten.")
        return

    try:
        for link in links:
            api_url = f"https://bisgram.com/api?api={api_key}&url={link}"
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as response:
                    data = await response.json()

                    if data.get("status") == "success":
                        shortened_link = data.get("shortenedUrl")
                        await message.reply(f"🔗 Shortened link: {shortened_link}")
                    else:
                        await message.reply("❌ Failed to shorten the link.")
    except Exception as e:
        print("Error shortening link:", e)
        await message.reply("❌ An error occurred while processing your link. Please try again.")

# Webhook setup
app = web.Application()
async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL)
app.on_startup.append(on_startup)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
