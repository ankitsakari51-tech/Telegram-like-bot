import aiohttp, os, asyncio, json, time, sys
from flask import Flask
from threading import Thread
from github import Github
import jwt  # PyJWT library for Token Expiry check
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# --- WEB SERVER (STABILITY FOR RENDER) ---
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
app = Flask('')

@app.route('/')
def home():
    # Render's health check needs a 200 OK response
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
REPO_NAME = "jjppjjpp0099-ux/OB53like-api"
JWT_API_URL = "https://xtytdtyj-jwt.up.railway.app/token"
LIKE_API = "https://ob-53like-api.vercel.app/like"
GRP_ID = -1002316321534

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# --- UTILITY & SECURITY FUNCTIONS ---
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def sc(t):
    """Converts normal text to Small Caps for better UI"""
    n, s = "abcdefghijklmnopqrstuvwxyz0123456789", "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ0123456789"
    return str(t).lower().translate(str.maketrans(n, s))

async def is_admin(u):
    """Verifies if the user is Ankit or Admin"""
    return str(u.id) == str(ADMIN_ID) or u.username == "ankitraj444"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# --- TOKEN EXPIRY & GITHUB LOGIC ---
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def check_token_expiry(token_data):
    """Checks if the first token in tokens.json is near expiry"""
    try:
        if not token_data or not isinstance(token_data, list) or len(token_data) == 0:
            return True
        
        token = token_data[0].get('token')
        if not token: return True

        # Decode JWT without signature verification
        payload = jwt.decode(token, options={"verify_signature": False})
        exp = payload.get('exp')
        
        # If less than 10 mins (600s) left, trigger refresh
        if exp and (time.time() + 600) > exp:
            print("[AUTO] Token expiring soon. Refreshing...")
            return True
        return False
    except Exception as e:
        print(f"[ERROR] Expiry Check: {e}")
        return True

async def github_push(content, commit_msg):
    """Pushes data to GitHub Repository"""
    try:
        g = Github(G_TOKEN)
        repo = g.get_repo(REPO_NAME)
        json_data = json.dumps(content, indent=4)
        
        try:
            file = repo.get_contents("tokens.json")
            repo.update_file(file.path, commit_msg, json_data, file.sha)
            print(f"[GITHUB] Update Success: {commit_msg}")
        except:
            repo.create_file("tokens.json", "Initial Creation", json_data)
            print("[GITHUB] File Created")
        return True
    except Exception as e:
        print(f"[CRITICAL] GitHub Error: {e}")
        return False

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# --- AUTO REFRESH BACKGROUND ENGINE ---
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def auto_refresh_task(application):
    """Background loop to keep tokens fresh 24/7"""
    print("[SYSTEM] Background Engine Started.")
    await asyncio.sleep(20) # Stability delay
    
    while True:
        try:
            g = Github(G_TOKEN)
            repo = g.get_repo(REPO_NAME)
            
            # 1. Read tokens.json
            try:
                t_file = repo.get_contents("tokens.json")
                tokens = json.loads(t_file.decoded_content.decode())
            except: tokens = []

            # 2. If expired, fetch new ones from Railway
            if check_token_expiry(tokens):
                u_file = repo.get_contents("uidpass.json")
                u_data = json.loads(u_file.decoded_content.decode())
                
                fresh_list = []
                async with aiohttp.ClientSession() as session:
                    for acc in u_data:
                        url = f"{JWT_API_URL}?uid={acc['uid']}&password={acc['password']}"
                        async with session.get(url) as r:
                            if r.status == 200:
                                res = await r.json()
                                if res.get("token"):
                                    fresh_list.append({"token": res.get("token")})
                
                # 3. Push new tokens back to GitHub
                if fresh_list:
                    if await github_push(fresh_list, "Automated Token Refresh"):
                        await application.bot.send_message(chat_id=ADMIN_ID, text="🔄 **Auto update done**")
            else:
                print("[AUTO] Tokens are fresh. Sleeping...")

        except Exception as e:
            print(f"[AUTO LOOP ERROR] {e}")
            
        await asyncio.sleep(60) # Check every 1 minute

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# --- TELEGRAM COMMAND HANDLERS ---
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

        # Custom logic for "Claimed" or success
        given = "+20" if status in [1, 2] else "Claimed"

        # Your Special Box Style
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
    except Exception as e:
        await wait.edit_text(f"❌ Error: {e}")

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
            if await github_push(json.loads(data.decode()), "Manual Update via Bot"):
                await msg.edit_text("✅ **Manual update done**")
            else:
                await msg.edit_text("❌ Failed to push.")
            c.user_data['waiting'] = False

async def check_sys(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if await is_admin(u.effective_user):
        try:
            g = Github(G_TOKEN)
            g.get_repo(REPO_NAME)
            await u.effective_chat.send_message(f"✅ System Online\nRepo: {REPO_NAME}")
        except: await u.effective_chat.send_message("❌ Repo Error")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# --- MAIN CORE RUNNER ---
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def main():
    print("[SYSTEM] Bot Initialization...")
    application = ApplicationBuilder().token(B_TOKEN).build()
    
    # Handlers Registration
    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("like", like_cmd))
    application.add_handler(CommandHandler("update", update_trigger))
    application.add_handler(CommandHandler("check", check_sys))
    application.add_handler(MessageHandler(filters.Document.ALL, doc_handler))
    
    # Run Auto-Refresh in Background
    asyncio.create_task(auto_refresh_task(application))
    
    # Start Polling
    async with application:
        await application.initialize()
        await application.start()
        print("[SYSTEM] Bot is Live!")
        await application.updater.start_polling(drop_pending_updates=True)
        # Keep process alive
        await asyncio.Event().wait()

if __name__ == "__main__":
    # Start Flask Webserver
    flask_thread = Thread(target=run_flask_server, daemon=True)
    flask_thread.start()
    
    # Execute Bot
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("[SYSTEM] Shutdown.")
