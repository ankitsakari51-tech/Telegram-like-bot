import aiohttp, os, asyncio, time
from flask import Flask
from threading import Thread
from github import Github
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# --- CONFIGURATION (Environment Variables) ---
B_TOKEN = os.environ.get("BOT_TOKEN")
G_TOKEN = os.environ.get("G_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")
REPO = "jjppjjpp0099-ux/OB53like-api" 

# Aapka Vercel API link
API_BASE = "https://ob-53like-api.vercel.app"
API = f"{API_BASE}/like"

# Aapka Telegram Group ID
GRP = -1002316321534

# --- WEB SERVER (For Keep-Alive & API Notifications) ---
app = Flask('')

@app.route('/')
def home(): 
    return "Bot is Online and Active"

@app.route('/notify_update')
def notify_update():
    """Jab tokens update honge, Vercel API is route ko call karegi"""
    try:
        # Group mein auto-message bhejna
        asyncio.run_coroutine_threadsafe(
            bot.bot.send_message(
                chat_id=GRP, 
                text="✅ **ᴛᴏᴋᴇɴ ᴀᴜᴛᴏ ᴜᴘᴅᴀᴛᴇ ᴅᴏɴᴇ**\n\nꜰʀᴇsʜ ᴛᴏᴋᴇɴs ʜᴀᴠᴇ ʙᴇᴇɴ ᴜᴘᴅᴀᴛᴇᴅ ɪɴ ɢɪᴛʜᴜʙ ʀᴇᴘᴏsɪᴛᴏʀʏ. sʏsᴛᴇᴍ ɪs ɴᴏᴡ ʀᴜɴɴɪɴɢ ᴏɴ ɴᴇᴡ ᴛᴏᴋᴇɴs."
            ),
            loop
        )
        return "Notification Sent", 200
    except Exception as e:
        return str(e), 500

def run_flask():
    try:
        app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
    except:
        pass

# --- BACKGROUND AUTO-PINGER ---
async def auto_pinger():
    """Har 5 minute mein Vercel API ko trigger karega token check karne ke liye"""
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                # API ke trigger route ko hit karna
                async with session.get(f"{API_BASE}/trigger-update") as resp:
                    print(f"Auto-Pinger: Triggered API, Status: {resp.status}")
        except Exception as e:
            print(f"Auto-Pinger Error: {e}")
        
        # 300 seconds = 5 Minutes
        await asyncio.sleep(300)

# --- BOT HELPERS ---
def sc(t):
    if not t: return ""
    n = "abcdefghijklmnopqrstuvwxyz0123456789"
    s = "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ0123456789"
    return str(t).lower().translate(str.maketrans(n, s))

async def is_o(u):
    return str(u.id) == str(ADMIN_ID) or u.username == "ankitraj444"

# --- COMMAND HANDLERS ---
async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    chat, user = u.effective_chat, u.effective_user
    if chat.type == "private" and not await is_o(user):
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("DM OWNER", url="https://t.me/ankitraj444"),
            InlineKeyboardButton("GROUP", url="https://t.me/+pQxMtYP9OfxmZmE1")
        ]])
        await chat.send_message("⚠️ ᴘʀɪᴠᴀᴛᴇ ʙᴏᴛ. ᴜsᴇ ɪɴ ᴏꜰꜰɪᴄɪᴀʟ ɢʀᴏᴜᴘ.", reply_markup=kb)
    elif chat.id == GRP or await is_o(user):
        name = sc(user.first_name)
        await chat.send_message(f"ʜᴇʏ {name}!\nᴏᴡɴᴇʀ: @ankitraj444\n\nᴄᴏᴍᴍᴀɴᴅs:\n/like <ʀᴇɢɪᴏɴ> <ᴜɪᴅ>\n/update (ꜰᴏʀ ᴏᴡɴᴇʀ)\n/check (ꜰᴏʀ ᴏᴡɴᴇʀ)")

async def like(u: Update, c: ContextTypes.DEFAULT_TYPE):
    chat, user = u.effective_chat, u.effective_user
    
    # Permission Check
    if (chat.id != GRP and not await is_o(user)):
        return

    if len(c.args) < 2:
        await chat.send_message("❌ ᴜsᴇ: `/like ind 12345678`", parse_mode="Markdown")
        return
    
    reg, uid = c.args[0].lower(), c.args[1]
    msg = await chat.send_message("ᴘʀᴏᴄᴇssɪɴɢ ʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ... ⏳")
    
    try:
        async with aiohttp.ClientSession() as ses:
            async with ses.get(f"{API}?uid={uid}&server_name={reg}", timeout=60) as r:
                d = await r.json()
        
        if d.get("status") not in [1, 2]:
            await msg.edit_text(f"sᴏᴍᴇᴛʜɪɴɢ ᴡᴇɴᴛ ᴡʀᴏɴɢ! 😵\nᴍᴇssᴀɢᴇ: {d.get('error', 'Unknown Error')}")
            return
            
        res = (
            f"ㅤㅤㅤ!! ʜᴇʏ {sc(user.first_name)} !!\n"
            f"✪━━━━━━━━━━━━━━━✪\n"
            f"╭💝\n"
            f"│ꜱᴜᴄᴄᴇssꜰᴜʟʟʏ ʟɪᴋᴇ ꜱᴇɴᴛ\n"
            f"╰━━━━━━━━━━━━━━━✪\n\n"
            f"╭━⟮ ✦ ᴘʟᴀʏᴇʀ ɪɴꜰᴏ ✦ ⟯\n"
            f"│👤 ɴᴀᴍᴇ: {d.get('PlayerNickname')}\n"
            f"│🆔 ᴜɪᴅ: {uid}\n"
            f"│🌍 ʀᴇɢɪᴏɴ: {reg.upper()}\n"
            f"╰━━━━━━━━━━━━━━━✪\n\n"
            f"╭━⟮ ✦ ʟɪᴋᴇ ᴅᴇᴛᴀɪʟꜱ ✦ ⟯\n"
            f"│👍 ʙᴇꜰᴏʀᴇ: {d.get('LikesbeforeCommand')}\n"
            f"│❤️ ᴀꜰᴛᴇʀ:  {d.get('LikesafterCommand')}\n"
            f"│➕ ɢɪᴠᴇɴ:  +{d.get('LikesGivenByAPI')}\n"
            f"╰━━━━━━━━━━━━━━━✪"
        )
        await msg.edit_text(res)
    except Exception as e:
        await msg.edit_text(f"ᴇʀʀᴏʀ: ᴄᴏɴɴᴇᴄᴛɪᴏɴ ꜰᴀɪʟᴇᴅ 😵")

async def up(u: Update, c: ContextTypes.DEFAULT_TYPE):
    """Owner command to manually upload tokens.json"""
    if await is_o(u.effective_user):
        c.user_data['u'] = True
        await u.effective_chat.send_message("📤 ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ `tokens.json` ꜰɪʟᴇ ɴᴏᴡ ᴛᴏ ᴜᴘᴅᴀᴛᴇ ɢɪᴛʜᴜʙ.")

async def check_repo(u: Update, c: ContextTypes.DEFAULT_TYPE):
    """Owner command to check GitHub and API status"""
    if await is_o(u.effective_user):
        m = await u.effective_chat.send_message("🔍 ᴄʜᴇᴄᴋɪɴɢ sʏsᴛᴇᴍ sᴛᴀᴛᴜs...")
        try:
            # GitHub Check
            g = Github(G_TOKEN)
            r = g.get_repo(REPO)
            files = [f.path for f in r.get_contents("")]
            
            # API Check
            async with aiohttp.ClientSession() as ses:
                async with ses.get(f"{API_BASE}/") as resp:
                    api_status = "Online" if resp.status == 200 else "Offline"

            status = (
                f"✅ **sʏsᴛᴇᴍ sᴛᴀᴛᴜs**\n\n"
                f"● ɢɪᴛʜᴜʙ: Connected\n"
                f"● ʀᴇᴘᴏ: `{REPO}`\n"
                f"● ᴛᴏᴋᴇɴs.ᴊsᴏɴ: {'Found' if 'tokens.json' in files else 'Missing'}\n"
                f"● ᴀᴘɪ sᴛᴀᴛᴜs: {api_status}\n"
            )
            await m.edit_text(status, parse_mode="Markdown")
        except Exception as e:
            await m.edit_text(f"❌ ᴇʀʀᴏʀ: {str(e)}")

async def handle_docs(u: Update, c: ContextTypes.DEFAULT_TYPE):
    """Handle the uploaded tokens.json file"""
    if c.user_data.get('u') and await is_o(u.effective_user):
        doc = u.message.document
        if doc and doc.file_name == 'tokens.json':
            m = await u.effective_chat.send_message("⏳ ᴜᴘʟᴏᴀᴅɪɴɢ ᴛᴏ ɢɪᴛʜᴜʙ...")
            try:
                f = await c.bot.get_file(doc.file_id)
                b = await f.download_as_bytearray()
                
                g = Github(G_TOKEN)
                r = g.get_repo(REPO)
                contents = r.get_contents("tokens.json")
                r.update_file(contents.path, "Manual Update via Bot", bytes(b), contents.sha)
                
                await m.edit_text("✅ **ɢɪᴛʜᴜʙ ᴜᴘᴅᴀᴛᴇᴅ sᴜᴄᴄᴇssꜰᴜʟʟʏ!**")
            except Exception as e:
                await m.edit_text(f"❌ ꜰᴀɪʟᴇᴅ: {e}")
            c.user_data['u'] = False

# --- MAIN RUNNER ---
if __name__ == "__main__":
    # Create global loop for thread safety
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # 1. Start Flask in a background thread
    Thread(target=run_flask, daemon=True).start()
    
    # 2. Start Auto-Pinger in a background thread
    def start_pinger_loop():
        asyncio.run(auto_pinger())
    Thread(target=start_pinger_loop, daemon=True).start()

    # 3. Build and Start Telegram Bot
    bot = ApplicationBuilder().token(B_TOKEN).build()
    
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("like", like))
    bot.add_handler(CommandHandler("update", up))
    bot.add_handler(CommandHandler("check", check_repo))
    bot.add_handler(MessageHandler(filters.Document.ALL, handle_docs))
    
    print("Bot is starting...")
    bot.run_polling(drop_pending_updates=True)
