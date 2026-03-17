import aiohttp
import asyncio
import os
from flask import Flask
from threading import Thread
from github import Github
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# --- RENDER DUMMY SERVER ---
app = Flask('')
@app.route('/')
def home():
    return "Bot is Alive!"

def run_web():
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run_web)
    t.start()
# --------------------------------------------------

# Tokens (Render Environment Variables se uthayega)
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
G_TOKEN = os.environ.get("G_TOKEN") 
REPO_NAME = "jjppjjpp0099-ux/Like-api-2"

OWNER_NAME = "@ankitraj444"
API_URL = "https://like-api-2-zy52.vercel.app/like"
ALLOWED_GROUP = -1002316321534 

# --- UTILS ---
def small_caps(text: str) -> str:
    normal = "abcdefghijklmnopqrstuvwxyz"
    small = "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ"
    return text.lower().translate(str.maketrans(normal, small))

async def send_styled(update: Update, text: str):
    await update.effective_chat.send_message(small_caps(text))

async def private_message(update: Update):
    buttons = [[
        InlineKeyboardButton("DM OWNER", url="https://t.me/ankitraj444"),
        InlineKeyboardButton("LIKE GROUP", url="https://t.me/+pQxMtYP9OfxmZmE1")
    ]]
    reply_markup = InlineKeyboardMarkup(buttons)
    await update.effective_chat.send_message(
        "⚠️ This bot is private. Use it only in the official group.",
        reply_markup=reply_markup
    )

# --- NAYA GITHUB UPDATE LOGIC ---
async def update_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Security: Sirf aapka username hi ise use kar sake (Taki group me koi aur na kare)
    if update.effective_user.username != "ankitraj444": 
        await update.message.reply_text("❌ Only the bot owner can update files.")
        return
        
    context.user_data['waiting_for_json'] = True
    await update.message.reply_text("📤 Okay! Ab koi bhi `.json` file bhejiye. Iska code dono GitHub files mein paste ho jayega.")

async def handle_json_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('waiting_for_json'):
        return

    doc = update.message.document
    if not doc or not doc.file_name.endswith('.json'):
        await update.message.reply_text("❌ Please send a valid `.json` file.")
        return
    
    status_msg = await update.message.reply_text(f"⏳ Reading `{doc.file_name}` and updating GitHub...")
    
    try:
        # 1. Jo file aapne bheji uska content download karna
        tg_file = await context.bot.get_file(doc.file_id)
        new_content_bytes = await tg_file.download_as_bytearray()
        new_content = bytes(new_content_bytes)

        # 2. GitHub Connection
        g = Github(G_TOKEN)
        repo = g.get_repo(REPO_NAME)
        
        # In dono files mein aapka naya code paste hoga
        files_to_update = ["token_ind.json", "token_ind_visit.json"]
        
        for file_name in files_to_update:
            contents = repo.get_contents(file_name)
            repo.update_file(
                contents.path, 
                f"Sync update from {doc.file_name}", 
                new_content, 
                contents.sha
            )
        
        await status_msg.edit_text(f"✅ Success! Content of `{doc.file_name}` pasted into `token_ind.json` & `token_ind_visit.json`.")
        context.user_data['waiting_for_json'] = False

    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {str(e)}")

# --- PURANE COMMANDS (LIKE, START, HELP) ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ALLOWED_GROUP:
        await private_message(update)
        return
    user_name = update.effective_user.first_name
    msg = (f"Hey! {user_name} nice to meet you 😊\n\n👑 owner: {OWNER_NAME}\n\n"
           "📌 available command:\n/like region uid\n\nexample:\n/like ind 123456789\n"
           "more command type /help")
    await send_styled(update, msg)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ALLOWED_GROUP:
        await private_message(update)
        return
    msg = ("📖 HELP MENU\n\n✅ /start - Bot start\n✅ /like region uid - Free Fire likes\n✅ /update - Update JSON files\n\n"
           f"👑 Owner: {OWNER_NAME}")
    await send_styled(update, msg)

async def like_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ALLOWED_GROUP:
        await private_message(update)
        return
    if len(context.args) < 2:
        await send_styled(update, "use: /like region uid\nexample: /like ind 123456789")
        return

    region, uid = context.args[0].lower(), context.args[1]
    await send_styled(update, "fetching player data... ⏳")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_URL}?uid={uid}&server_name={region}") as response:
                data = await response.json()

        if data.get("status") != 1:
            await send_styled(update, "Try next day api error 😵")
            return

        name = data.get("PlayerNickname", "Unknown")
        before = data.get("LikesbeforeCommand", 0)
        after = data.get("LikesafterCommand", 0)
        given = data.get("LikesGivenByAPI", 0)

        msg = f"🔥 PLAYER PROFILE\n\n👤 Name : {name}\n🆔 UID : {uid}\n🌍 Region : {region}\n\n" \
              f"👍 Before Likes : {before}\n❤️ Likes Given : +{given}\n🔥 After Likes : {after}"
        await send_styled(update, msg)
    except:
        await send_styled(update, "api error aa gaya 😵")

def main():
    keep_alive()
    app_tele = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Purane Handlers
    app_tele.add_handler(CommandHandler("start", start_command))
    app_tele.add_handler(CommandHandler("help", help_command))
    app_tele.add_handler(CommandHandler("like", like_command))
    
    # Naye GitHub Handlers
    app_tele.add_handler(CommandHandler("update", update_command))
    app_tele.add_handler(MessageHandler(filters.Document.ALL, handle_json_file))
    
    print("Bot is running with Multi-File Update feature...")
    app_tele.run_polling()

if __name__ == "__main__":
    main()
