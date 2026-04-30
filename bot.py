import aiohttp, os, asyncio, json, time, sys
from flask import Flask
from threading import Thread
from github import Github
import jwt  # PyJWT library
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# --- WEB SERVER (STABILITY FOR RENDER) ---
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
app = Flask('')

@app.route('/')
def home():
    return {
        "status": "online",
        "bot": "GT BOT",
        "server": "Active"
    }, 200

def run_flask_server():
    try:
        port = int(os.environ.get("PORT", 10000))
        print(f"[SYSTEM] Flask running on port {port}")
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    except Exception as e:
        print(f"[CRITICAL] Web Server Error: {e}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# --- CONFIGURATION (ENV VARIABLES) ---
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
B_TOKEN = os.environ.get("BOT_TOKEN")
G_TOKEN = os.environ.get("G_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")
REPO_NAME = "jjppjjpp0099-ux/OB53like-api"  # Yeh backend mein kaam karega
JWT_API_URL = "https://xtytdtyj-jwt.up.railway.app/token"
LIKE_API = "https://ob-53like-api.vercel.app/like"
GRP_ID = -1002316321534

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# --- UTILITY & SECURITY FUNCTIONS ---
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def sc(t):
    """Converts text to Small Caps for UI"""
    n, s = "abcdefghijklmnopqrstuvwxyz0123456789", "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ0123456789"
    return str(t).lower().translate(str.maketrans(n, s))

async def is_admin(u):
    """Checks if user is Owner or Admin"""
    return str(u.id) == str(ADMIN_ID) or u.username == "ankitraj444"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# --- TOKEN & GITHUB ENGINE ---
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def check_token_expiry(token_data):
    try:
        if not token_data or not isinstance(token_data, list) or len(token_data) == 0:
            return True
        t = token_data[0].get('token')
        if not t: return True
        payload = jwt.decode(t, options={"verify_signature": False})
        exp = payload.get('exp')
        return (time.time() + 600) > exp if exp else True
    except: return True

async def github_push(content, commit_msg):
    try:
        g = Github(G_TOKEN)
        repo = g.get_repo(REPO_NAME)
        json_data = json.dumps(content, indent=4)
        try:
            f = repo.get_contents("tokens.json")
            repo.update_file(f.path, commit_msg, json_data, f.sha)
        except:
            repo.create_file("tokens.json", "Initial", json_data)
        return True
    except: return False

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# --- AUTO REFRESH TASK ---
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def auto_refresh_task(application):
    print("[SYSTEM] Background Engine Started.")
    await asyncio.sleep(15) 
    while True:
        try:
            g = Github(G_TOKEN)
            repo = g.get_repo(REPO_NAME)
            try:
                t_file = repo.get_contents("tokens.json")
                tokens = json.loads(t_file.decoded_content.decode())
            except: tokens = []

            if check_token_expiry(tokens):
                u_file = repo.get_contents("uidpass.json")
                u_data = json.loads(u_file.decoded_content.decode())
                fresh = []
                async with aiohttp.ClientSession() as session:
                    for acc in u_data:
                        async with session.get(f"{JWT_API_URL}?uid={acc['uid']}&password={acc['password']}") as r:
                            if r.status == 200:
                                res = await r.json()
                                if res.get("token"): fresh.append({"token": res.get("token")})
                if fresh:
                    await github_push(fresh, "Auto-Update")
                    await application.bot.send_message(chat_id=ADMIN_ID, text="🔄 **Auto update done**")
        except: pass
        await asyncio.sleep(60)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# --- BOT COMMAND HANDLERS ---
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def start_cmd(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if u.effective_chat.id == GRP_ID or await is_admin(u.effective_user):
        name = sc(u.effective_user.first_name)
        text = (
            f"!! ʜᴇʏ {name} !!\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "ᴏᴡɴᴇʀ: @ankitraj444\n"
            "sᴛᴀᴛᴜs: ᴏɴʟɪɴᴇ ✅\n\n"
            "📜 Commands:\n"
            "➥ /like [region] [uid]\n"
            "➥ /update - Manual Update\n"
            "➥ /check - System Check"
        )
        await u.effective_chat.send_message(text)

async def like_cmd(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if not (u.effective_chat.id == GRP_ID or await is_admin(u.effective_user)): return
    if len(c.args) < 2:
        await u.effective_chat.send_message("❌ /like [region] [uid]")
        return
    
    reg, uid = c.args[0].lower(), c.args[1]
    wait = await u.effective_chat.send_message("⌛ ᴘʀᴏᴄᴇssɪɴɢ...")

    try:
        async with aiohttp.ClientSession() as ses:
            async with ses.get(f"{LIKE_API}?uid={uid}&server_name={reg}") as r:
                d = await r.json()
        
        name = d.get('PlayerNickname', 'Unknown')
        before = d.get('LikesbeforeCommand', '0')
        after = d.get('LikesafterCommand', '0')
        status = d.get("status")
        given = "+20" if status in [1, 2] else "Claimed"

        # Box Style Design
        final = (
            f"ㅤㅤㅤ!! ʜᴇʏ ᴀɴᴋɪᴛ !!\n"
            f"✪━━━━━━━━━━━━━━━✪\n"
            f"╭💝\n"
            f"│ꜱᴜᴄᴄᴇssꜰᴜʟʟʏ ʟɪᴋᴇ ꜱᴇɴᴛ\n"
            f"╰━━━━━━━━━━━━━━━✪\n\n"
            f"╭━⟮ ✦ ᴘʟᴀʏᴇʀ ɪɴꜰᴏ ✦ ⟯\n"
            f"│👤 ɴᴀᴍᴇ: {name}\n"
            f"│🆔 ᴜɪᴅ: {uid}\n"
            f"│🌍 ʀᴇɢɪᴏɴ: {reg.upper()}\n"
            f"╰━━━━━━━━━━━━━━━✪\n\n"
            f"╭━⟮ ✦ ʟɪᴋᴇ ᴅᴇᴛᴀɪʟꜱ ✦ ⟯\n"
            f"│👍 ʟɪᴋᴇs ʙᴇꜰᴏʀᴇ:  {before}\n"
            f"│❤️ ʟɪᴋᴇs ᴀꜰᴛᴇʀ:    {after}\n"
            f"│➕ ʟɪᴋᴇs ɢɪᴠᴇɴ:   {given}\n"
            f"╰━━━━━━━━━━━━━━━✪"
        )
        await wait.edit_text(final)
    except: await wait.edit_text("😵 API Connection Lost")

async def update_trigger(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if await is_admin(u.effective_user):
        c.user_data['waiting'] = True
        await u.effective_chat.send_message("📤 Send `tokens.json` file now.")

async def doc_handler(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if c.user_data.get('waiting') and await is_admin(u.effective_user):
        doc = u.message.document
        if doc.file_name.endswith('.json'):
            msg = await u.effective_chat.send_message("⏳ Updating GitHub...")
            f = await c.bot.get_file(doc.file_id)
            data = await f.download_as_bytearray()
            if await github_push(json.loads(data.decode()), "Manual Update"):
                await msg.edit_text("✅ **Manual update done**")
            else: await msg.edit_text("❌ Failed.")
            c.user_data['waiting'] = False

async def check_sys(u: Update, c: ContextTypes.DEFAULT_TYPE):
    """System Check with Hidden Repo Name"""
    if await is_admin(u.effective_user):
        m = await u.effective_chat.send_message("🔍 Checking...")
        try:
            g = Github(G_TOKEN)
            g.get_repo(REPO_NAME)
            # Private Message Format
            await m.edit_text("✅ **Connected!**\nRepo: `OB53`\nBot Status: Active")
        except: await m.edit_text("❌ Connection Error")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# --- MAIN RUNNER ---
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def main():
    application = ApplicationBuilder().token(B_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("like", like_cmd))
    application.add_handler(CommandHandler("update", update_trigger))
    application.add_handler(CommandHandler("check", check_sys))
    application.add_handler(MessageHandler(filters.Document.ALL, doc_handler))
    
    asyncio.create_task(auto_refresh_task(application))
    
    async with application:
        await application.initialize()
        await application.start()
        print("[SYSTEM] Bot Started Successfully.")
        await application.updater.start_polling(drop_pending_updates=True)
        await asyncio.Event().wait()

if __name__ == "__main__":
    Thread(target=run_flask_server, daemon=True).start()
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit): pass
