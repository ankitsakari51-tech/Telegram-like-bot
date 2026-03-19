import aiohttp
import asyncio
import os
import requests
from flask import Flask
from threading import Thread
from github import Github
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# --- 1. ANTI-SLEEP WEB SERVER ---
app = Flask('')
@app.route('/')
def home():
    return "Bot is Running 24/7!"

def run_web():
    # Render ke liye port setup
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.daemon = True
    t.start()

# --- 2. CONFIGURATION ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
G_TOKEN = os.environ.get("G_TOKEN") 
REPO_NAME = "jjppjjpp0099-ux/Like-api-2"
ADMIN_ID = os.environ.get("ADMIN_ID")

OWNER_NAME = "@ankitraj444"
API_URL = "https://like-api-2-zy52.vercel.app/like"
ALLOWED_GROUP = -1002316321534 

# --- 3. UTILS & SECURITY ---
def small_caps(text: str) -> str:
    normal = "abcdefghijklmnopqrstuvwxyz"
    small = "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ"
    return text.lower().translate(str.maketrans(normal, small))

async def is_owner(update: Update):
    user = update.effective_user
    # Dono check: ID aur Username
    return str(user.id) == str(ADMIN_ID) or user.username == "ankitraj444"

async def send_private_error(update: Update):
    buttons = [[
        InlineKeyboardButton("DM OWNER", url="https://t.me/ankitraj444"),
        InlineKeyboardButton("LIKE GROUP", url="https://t.me/+pQxMtYP9OfxmZmE1")
    ]]
    reply_markup = InlineKeyboardMarkup(buttons)
    await update.effective_chat.send_message(
        "⚠️ This bot is private. Use it only in the official group.",
        reply_markup=reply_markup
    )

# --- 4. GITHUB UPDATE LOGIC ---
async def update_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_owner(update):
        return 

    context.user_data['waiting_for_json'] = True
    await update.message.reply_text("📤 Okay Boss! Ab `.json` file bhejiye, main GitHub update kar dunga.")

async def handle_json_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('waiting_for_json') or not await is_owner(update):
        return

    doc = update.message.document
    if not doc or not doc.file_name.endswith('.json'):
        await update.message.reply_text("❌ Please send a valid `.json` file.")
        return
    
    status_msg = await update.message.reply_text("⏳ Updating GitHub... Auto-deploy will start soon.")
    
    try:
        tg_file = await context.bot.get_file(doc.file_id)
        new_content_bytes = await tg_file.download_as_bytearray()

        g = Github(G_TOKEN)
        repo = g.get_repo(REPO_NAME)
        files_to_update = ["token_ind.json", "token_ind_visit.json"]
        
        for file_name in files_to_update:
            contents = repo.get_contents(file_name)
            repo.update_file(contents.path, "Auto-update via Bot", bytes(new_content_bytes), contents.sha)
        
        await status_msg.edit_text("✅ Success! GitHub Updated. Bot will restart automatically.")
        context.user_data['waiting_for_json'] = False
    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {str(e)}")

# --- 5. COMMAND HANDLERS ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    owner_check = await is_owner(update)

    # DM User Restriction
    if update.effective_chat.type == "private" and not owner_check:
        await send_private_error(update)
        return

    # Group Check (for non-owners)
    if chat_id != ALLOWED_GROUP and not owner_check:
        return

    user_name = update.effective_user.first_name
    msg = f"Hey! {user_name} nice to meet you 😊\n\n👑 owner: {OWNER_NAME}\n\n📌 Commands:\n/like region uid\n/help"
    await update.effective_chat.send_message(small_caps(msg))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    owner_check = await is_owner(update)

    if update.effective_chat.type == "private" and not owner_check:
        await send_private_error(update)
        return

    if chat_id != ALLOWED_GROUP and not owner_check:
        return
    
    msg = "📖 HELP MENU\n\n✅ /start - Start\n✅ /like region uid - FF Likes\n✅ /update - Admin Only"
    await update.effective_chat.send_message(small_caps(msg))

async def like_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    owner_check = await is_owner(update)

    if update.effective_chat.type == "private" and not owner_check:
        await send_private_error(update)
        return

    if chat_id != ALLOWED_GROUP and not owner_check:
        return

    if len(context.args) < 2:
        await update.message.reply_text(small_caps("use: /like region uid"))
        return

    region, uid = context.args[0].lower(), context.args[1]
    status_msg = await update.message.reply_text("fetching player data... ⏳")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_URL}?uid={uid}&server_name={region}") as response:
                data = await response.json()

        if data.get("status") != 1:
            await status_msg.edit_text("Try next day api error 😵")
            return

        name = data.get("PlayerNickname")
        before = data.get("LikesbeforeCommand")
        given = data.get("LikesGivenByAPI")
        after = data.get("LikesafterCommand")
        
        msg = f"👤 Name : {name}\n👍 Before : {before}\n❤️ Added : +{given}\n🔥 After : {after}"
        await status_msg.edit_text(msg)
    except:
        await status_msg.edit_text("api error aa gaya 😵")

# --- 6. MAIN ---
def main():
    keep_alive()
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("like", like_command))
    application.add_handler(CommandHandler("update", update_command))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_json_file))
    
    print("Bot is Live...")
    # drop_pending_updates conflict se bachne ke liye zaroori hai
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    owner_check = await is_owner(update)

    if chat_id != ALLOWED_GROUP and not owner_check:
        await send_private_error(update)
        return
    
    msg = "📖 HELP MENU\n\n✅ /start - Start\n✅ /like region uid - FF Likes\n✅ /update - Admin Only"
    await send_styled(update, msg)

async def send_styled(update: Update, text: str):
    await update.effective_chat.send_message(small_caps(text))

async def like_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    owner_check = await is_owner(update)

    if chat_id != ALLOWED_GROUP and not owner_check:
        await send_private_error(update)
        return

    if len(context.args) < 2:
        await send_styled(update, "use: /like region uid")
        return

    region, uid = context.args[0].lower(), context.args[1]
    status_msg = await update.message.reply_text("fetching player data... ⏳")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_URL}?uid={uid}&server_name={region}") as response:
                data = await response.json()

        if data.get("status") != 1:
            await status_msg.edit_text("Try next day api error 😵")
            return

        name, before, given, after = data.get("PlayerNickname"), data.get("LikesbeforeCommand"), data.get("LikesGivenByAPI"), data.get("LikesafterCommand")
        msg = f"👤 Name : {name}\n👍 Before : {before}\n❤️ Added : +{given}\n🔥 After : {after}"
        await status_msg.edit_text(msg)
    except:
        await status_msg.edit_text("api error aa gaya 😵")

# --- 6. MAIN EXECUTION ---
def main():
    keep_alive() # Start Web Server
    app_tele = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app_tele.add_handler(CommandHandler("start", start_command))
    app_tele.add_handler(CommandHandler("help", help_command))
    app_tele.add_handler(CommandHandler("like", like_command))
    app_tele.add_handler(CommandHandler("update", update_command))
    app_tele.add_handler(MessageHandler(filters.Document.ALL, handle_json_file))
    
    print("Bot is Live with Anti-Sleep & Multi-File Update...")
    app_tele.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
