import aiohttp, os, asyncio, json
from flask import Flask, request
from threading import Thread
from github import Github
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# --- Config & IDs ---
B_TOKEN = os.environ.get("BOT_TOKEN")
G_TOKEN = os.environ.get("G_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")
# Naya Repo Path
REPO = "jjppjjpp0099-ux/OB53like-api"
API = "https://ob-53like-api.vercel.app/like"
GRP = -1002316321534

# --- Web Server ---
app = Flask('')

@app.route('/')
def home(): return "Bot is Online"

# Ye endpoint update_tokens.py call karega message bhejne ke liye
@app.route('/update_notify')
def update_notify():
    # Hum isse async function call karenge telegram message ke liye
    return "Notification Received", 200

def run():
    try:
        app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
    except Exception: pass

# --- Font Converter ---
def sc(t):
    if not t: return ""
    n = "abcdefghijklmnopqrstuvwxyz0123456789"
    s = "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ0123456789"
    trans = str.maketrans(n, s)
    return str(t).lower().translate(trans)

async def is_o(u):
    return str(u.id) == str(ADMIN_ID) or u.username == "ankitraj444"

# --- Bot Handlers ---
async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    chat, user = u.effective_chat, u.effective_user
    if chat.id == GRP or await is_o(user):
        name = sc(user.first_name)
        await chat.send_message(f"Hey {name}!\nOwner: @ankitraj444\nCommands: /like, /update")

async def like(u: Update, c: ContextTypes.DEFAULT_TYPE):
    chat, user = u.effective_chat, u.effective_user
    if (chat.id != GRP and not await is_o(user)): return
    if len(c.args) < 2:
        await chat.send_message("❌ Use: /like region uid")
        return
    
    reg, uid = c.args[0].lower(), c.args[1]
    msg = await chat.send_message("⚡ Processing...")
    
    try:
        async with aiohttp.ClientSession() as ses:
            async with ses.get(f"{API}?uid={uid}&server_name={reg}") as r:
                d = await r.json()
        
        if r.status != 200 or d.get("status") not in [1, 2]:
            await msg.edit_text("❌ API Error or Token Expired.")
            return
            
        res = (
            f"ㅤㅤㅤ!! ʜᴇʏ {sc(user.first_name)} !!\n"
            f"━━━━━━━━━━━━━━━\n"
            f"👤 ɴᴀᴍᴇ: {d.get('PlayerNickname')}\n"
            f"🆔 ᴜɪᴅ: {uid}\n"
            f"🌍 ʀᴇɢɪᴏɴ: {reg.upper()}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"👍 ʙᴇꜰᴏʀᴇ: {d.get('LikesbeforeCommand')}\n"
            f"❤️ ᴀꜰᴛᴇʀ: {d.get('LikesafterCommand')}\n"
            f"➕ ɢɪᴠᴇɴ: +{d.get('LikesGivenByAPI')}"
        )
        await msg.edit_text(res)
    except Exception:
        await msg.edit_text("System Busy 😵")

async def up(u: Update, c: ContextTypes.DEFAULT_TYPE):
    """Manual Update Command: Send .json file to update OB53like-api/tokens.json"""
    if await is_o(u.effective_user):
        c.user_data['u'] = True
        await u.effective_chat.send_message("📤 Send new tokens.json file to update GitHub.")

async def doc(u: Update, c: ContextTypes.DEFAULT_TYPE):
    """Handles manual JSON file upload"""
    if c.user_data.get('u') and await is_o(u.effective_user):
        d = u.message.document
        if d and d.file_name.endswith('.json'):
            m = await u.effective_chat.send_message("⏳ Updating GitHub tokens.json...")
            try:
                f = await c.bot.get_file(d.file_id)
                b = await f.download_as_bytearray()
                
                # Update in NEW REPO
                r = Github(G_TOKEN).get_repo(REPO)
                rf = r.get_contents("tokens.json")
                r.update_file(rf.path, "Manual Update", bytes(b), rf.sha)
                
                await m.edit_text("✅ GitHub: tokens.json Updated Successfully!")
            except Exception as e:
                await m.edit_text(f"Update Failed: {e}")
            c.user_data['u'] = False

if __name__ == "__main__":
    Thread(target=run, daemon=True).start()
    bot = ApplicationBuilder().token(B_TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("like", like))
    bot.add_handler(CommandHandler("update", up))
    bot.add_handler(MessageHandler(filters.Document.ALL, doc))
    bot.run_polling(drop_pending_updates=True)
