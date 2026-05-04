# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GT BOT - FULL HEAVY VERSION (PRIVATE REPO MODE)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import aiohttp
import os
import asyncio
import json
import time
import sys
import logging
import jwt  # PyJWT library for Token Expiry check
from flask import Flask
from threading import Thread
from github import Github
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# --- Logging Setup (Jaisa Render logs mein dikhta hai) ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# --- WEB SERVER (STABILITY FOR RENDER) ---
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
app = Flask('')

@app.route('/')
def home():
    """Render's health check needs a 200 OK response"""
    return {
        "status": "online",
        "bot": "GT BOT",
        "server": "Active",
        "owner": "ankitraj444"
    }, 200

def run_flask_server():
    try:
        port = int(os.environ.get("PORT", 10000))
        print(f"--> [SYSTEM] Starting Flask server on port {port}...")
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    except Exception as e:
        print(f"--> [CRITICAL] Web Server Error: {e}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# --- CONFIGURATION (ENV VARIABLES) ---
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
B_TOKEN = os.environ.get("BOT_TOKEN")
G_TOKEN = os.environ.get("G_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")
REPO_NAME = "jjppjjpp0099-ux/OB53like-api"  # Backend ID
JWT_API_URL = "https://xtytdtyj-jwt.up.railway.app/token"
LIKE_API = "https://ob-53like-api.vercel.app/like"
GRP_ID = -1002316321534

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# --- UTILITY & SECURITY FUNCTIONS ---
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def sc(t):
    """Converts text to Small Caps for Premium UI"""
    normal = "abcdefghijklmnopqrstuvwxyz0123456789"
    fancy = "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ0123456789"
    return str(t).lower().translate(str.maketrans(normal, fancy))

async def is_admin(u):
    """Verifies if the user is Ankit or Admin"""
    if not u: return False
    return str(u.id) == str(ADMIN_ID) or u.username == "ankitraj444"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# --- TOKEN & GITHUB ENGINE ---
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def check_token_expiry(token_data):
    """Checks if tokens in tokens.json are still valid using PyJWT"""
    try:
        print("--> [AUTO] Checking token validity...")
        if not token_data or not isinstance(token_data, list) or len(token_data) == 0:
            print("--> [AUTO] tokens.json is empty or invalid.")
            return True
        
        t = token_data[0].get('token')
        if not t: return True

        # Decode JWT to check 'exp'
        payload = jwt.decode(t, options={"verify_signature": False})
        exp = payload.get('exp')
        
        # Buffer of 10 minutes (600s)
        is_expired = (time.time() + 600) > exp if exp else True
        if is_expired:
            print("--> [AUTO] Token expired or near expiry.")
        else:
            print(f"--> [AUTO] Token valid. Expires in {int(exp - time.time())}s")
        return is_expired
    except Exception as e:
        print(f"--> [ERROR] Expiry Check failed: {e}")
        return True

async def github_push(content, commit_msg):
    """Reliable GitHub File Update Engine"""
    try:
        print(f"--> [GITHUB] Attempting to push: {commit_msg}")
        g = Github(G_TOKEN)
        repo = g.get_repo(REPO_NAME)
        json_string = json.dumps(content, indent=4)
        
        try:
            f = repo.get_contents("tokens.json")
            repo.update_file(f.path, commit_msg, json_string, f.sha)
            print("--> [GITHUB] tokens.json updated successfully.")
        except:
            repo.create_file("tokens.json", "Initial Creation", json_string)
            print("--> [GITHUB] tokens.json created as new file.")
        return True
    except Exception as e:
        print(f"--> [CRITICAL] GitHub Push Error: {e}")
        return False

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# --- AUTO REFRESH BACKGROUND LOOP ---
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def auto_refresh_engine(application):
    """Har 1 minute mein check karega aur expire hote hi update karega"""
    print("--> [SYSTEM] Background Auto-Refresh Engine Started.")
    await asyncio.sleep(20) # Start stability delay
    
    while True:
        try:
            g = Github(G_TOKEN)
            repo = g.get_repo(REPO_NAME)
            
            # 1. tokens.json load karo
            try:
                t_file = repo.get_contents("tokens.json")
                tokens = json.loads(t_file.decoded_content.decode())
            except:
                tokens = []

            # 2. Check if refresh needed
            if check_token_expiry(tokens):
                print("--> [AUTO] Fetching fresh credentials from uidpass.json...")
                u_file = repo.get_contents("uidpass.json")
                u_data = json.loads(u_file.decoded_content.decode())
                
                fresh_tokens = []
                async with aiohttp.ClientSession() as session:
                    for acc in u_data:
                        api_url = f"{JWT_API_URL}?uid={acc['uid']}&password={acc['password']}"
                        async with session.get(api_url) as r:
                            if r.status == 200:
                                res = await r.json()
                                if res.get("token"):
                                    fresh_tokens.append({"token": res.get("token")})
                
                # 3. GitHub par push karo
                if fresh_tokens:
                    if await github_push(fresh_tokens, "Automated Token Refresh Engine"):
                        await application.bot.send_message(chat_id=ADMIN_ID, text="🔄 **Auto update done**")
                else:
                    print("--> [AUTO] Failed to fetch new tokens from Railway API.")
            else:
                print("--> [AUTO] No update required at this time.")

        except Exception as e:
            print(f"--> [AUTO LOOP ERROR] {e}")
            
        await asyncio.sleep(60) # Har 1 minute mein check

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# --- TELEGRAM COMMAND HANDLERS ---
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def start_cmd(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if u.effective_chat.id == GRP_ID or await is_admin(u.effective_user):
        name = sc(u.effective_user.first_name)
        welcome_text = (
            f"!! ʜᴇʏ {name} !!\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "ᴏᴡɴᴇʀ: @ankitraj444\n"
            "sᴛᴀᴛᴜs: ᴏɴʟɪɴᴇ ✅\n\n"
            "📜 ᴄᴏᴍᴍᴀɴᴅs:\n"
            "➥ /like [ʀᴇɢɪᴏɴ] [ᴜɪᴅ]\n"
            "➥ /update - ᴍᴀɴᴜᴀʟ ᴛᴏᴋᴇɴ ᴜᴘᴅᴀᴛᴇ\n"
            "➥ /check - ʀᴇᴘᴏ ᴄᴏɴɴᴇᴄᴛɪᴠɪᴛʏ\n"
            "━━━━━━━━━━━━━━━━━━━━"
        )
        await u.effective_chat.send_message(welcome_text)

async def like_cmd(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if not (u.effective_chat.id == GRP_ID or await is_admin(u.effective_user)): return
    
    if len(c.args) < 2:
        await u.effective_chat.send_message("❌ Usage: /like [region] [uid]")
        return
    
    reg, uid = c.args[0].lower(), c.args[1]
    wait_msg = await u.effective_chat.send_message("⌛ ᴘʀᴏᴄᴇssɪɴɢ...")

    try:
        async with aiohttp.ClientSession() as ses:
            async with ses.get(f"{LIKE_API}?uid={uid}&server_name={reg}") as r:
                d = await r.json()
        
        name = d.get('PlayerNickname', 'Unknown')
        before = d.get('LikesbeforeCommand', '0')
        after = d.get('LikesafterCommand', '0')
        status = d.get("status")

        # Logic for "Claimed" or success
        given = "+20" if status in [1, 2] else "Claimed"

        # Special Box Style Design
        final_box = (
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
        await wait_msg.edit_text(final_box)
    except Exception as e:
        await wait_msg.edit_text(f"😵 API Error: {e}")

async def update_trigger(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if await is_admin(u.effective_user):
        c.user_data['waiting_for_file'] = True
        await u.effective_chat.send_message("📤 ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ `tokens.json` ꜰɪʟᴇ ᴛᴏ ᴜᴘᴅᴀᴛᴇ ᴍᴀɴᴜᴀʟʟʏ.")

async def file_handler(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if c.user_data.get('waiting_for_file') and await is_admin(u.effective_user):
        doc = u.message.document
        if doc.file_name.endswith('.json'):
            msg = await u.effective_chat.send_message("⏳ ᴜᴘʟᴏᴀᴅɪɴɢ ᴛᴏ ɢɪᴛʜᴜʙ...")
            try:
                tg_file = await c.bot.get_file(doc.file_id)
                content_bytes = await tg_file.download_as_bytearray()
                json_data = json.loads(content_bytes.decode('utf-8'))
                
                if await github_push(json_data, "Manual Update via Telegram"):
                    await msg.edit_text("✅ **Manual update done**")
                else:
                    await msg.edit_text("❌ GitHub Push Failed.")
            except Exception as e:
                await msg.edit_text(f"❌ Error: {e}")
            c.user_data['waiting_for_file'] = False

async def check_sys(u: Update, c: ContextTypes.DEFAULT_TYPE):
    """Private Repo Connectivity Check"""
    if await is_admin(u.effective_user):
        wait = await u.effective_chat.send_message("🔍 ᴄʜᴇᴄᴋɪɴɢ...")
        try:
            g = Github(G_TOKEN)
            g.get_repo(REPO_NAME)
            # Private Format as requested
            await wait.edit_text("✅ **Connected!**\nRepo: `OB53`\nBot Status: Active")
        except Exception as e:
            await wait.edit_text(f"❌ Connection Error: {e}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# --- MAIN CORE RUNNER ---
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def main_runner():
    print("--> [SYSTEM] Initializing GT BOT Engine...")
    application = ApplicationBuilder().token(B_TOKEN).build()
    
    # Registering Handlers
    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("like", like_cmd))
    application.add_handler(CommandHandler("update", update_trigger))
    application.add_handler(CommandHandler("check", check_sys))
    application.add_handler(MessageHandler(filters.Document.ALL, file_handler))
    
    # Start Auto-Refresh Engine
    asyncio.create_task(auto_refresh_engine(application))
    
    # Start Polling (Custom loop for Render stability)
    async with application:
        await application.initialize()
        await application.start()
        print("--> [SYSTEM] Bot is Live and Polling.")
        await application.updater.start_polling(drop_pending_updates=True)
        # Keep alive
        stop_event = asyncio.Event()
        await stop_event.wait()

if __name__ == "__main__":
    # Start Flask Webserver in daemon thread
    flask_thread = Thread(target=run_flask_server, daemon=True)
    flask_thread.start()
    
    # Run the main async bot loop
    try:
        asyncio.run(main_runner())
    except (KeyboardInterrupt, SystemExit):
        print("--> [SYSTEM] Shutdown Signal Received.")
