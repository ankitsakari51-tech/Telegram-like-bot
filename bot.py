# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GT BOT - FULL HEAVY VERSION (PRIVATE REPO MODE)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import aiohttp
import os
import asyncio
import json
import time
import logging
import jwt  # PyJWT library for Token Expiry check
from flask import Flask
from threading import Thread
from github import Github
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# --- Logging Setup ---
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
ADMIN_ID = str(os.environ.get("ADMIN_ID", ""))
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
    return str(u.id) == ADMIN_ID or u.username == "ankitraj444"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# --- TOKEN & GITHUB ENGINE ---
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def check_token_expiry(token_data):
    try:
        print("--> [AUTO] Checking token validity...")
        if not token_data or not isinstance(token_data, list) or len(token_data) == 0:
            return True
        
        t = token_data[0].get('token')
        if not t: return True

        payload = jwt.decode(t, options={"verify_signature": False})
        exp = payload.get('exp')
        
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
    try:
        print(f"--> [GITHUB] Attempting to push: {commit_msg}")
        g = Github(G_TOKEN)
        repo = g.get_repo(REPO_NAME)
        json_string = json.dumps(content, indent=4)
        
        try:
            f = repo.get_contents("tokens.json")
            repo.update_file(f.path, commit_msg, json_string, f.sha)
        except:
            repo.create_file("tokens.json", "Initial Creation", json_string)
        return True
    except Exception as e:
        print(f"--> [CRITICAL] GitHub Push Error: {e}")
        return False

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# --- AUTO REFRESH BACKGROUND LOOP ---
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def auto_refresh_engine(application):
    print("-->[SYSTEM] Background Auto-Refresh Engine Started.")
    await asyncio.sleep(20)
    
    while True:
        try:
            g = Github(G_TOKEN)
            repo = g.get_repo(REPO_NAME)
            
            try:
                t_file = repo.get_contents("tokens.json")
                tokens = json.loads(t_file.decoded_content.decode())
            except:
                tokens = []

            if check_token_expiry(tokens):
                print("-->[AUTO] Fetching fresh credentials from uidpass.json...")
                u_file = repo.get_contents("uidpass.json")
                u_data = json.loads(u_file.decoded_content.decode())
                
                fresh_tokens =[]
                async with aiohttp.ClientSession() as session:
                    for acc in u_data:
                        api_url = f"{JWT_API_URL}?uid={acc['uid']}&password={acc['password']}"
                        async with session.get(api_url) as r:
                            if r.status == 200:
                                res = await r.json()
                                if res.get("token"):
                                    fresh_tokens.append({"token": res.get("token")})
                
                if fresh_tokens:
                    if await github_push(fresh_tokens, "Automated Token Refresh Engine"):
                        await application.bot.send_message(chat_id=ADMIN_ID, text="🔄 **Auto update done**")
            else:
                pass
        except Exception as e:
            print(f"--> [AUTO LOOP ERROR] {e}")
            
        await asyncio.sleep(60)

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
            "➥ /like[ʀᴇɢɪᴏɴ] [ᴜɪᴅ]\n"
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

    caller_name = sc(u.effective_user.first_name)

    try:
        async with aiohttp.ClientSession() as ses:
            async with ses.get(f"{LIKE_API}?uid={uid}&server_name={reg}") as r:
                d = await r.json()
                
                # Check if API returned an error specifically for Wrong UID
                if r.status != 200:
                    if "Invalid UID" in d.get("error", "") or "AccountNotFound" in str(d):
                        await wait_msg.edit_text("❌ Wrong Player UID")
                        return
                    else:
                        await wait_msg.edit_text(f"😵 API Error: {d.get('error', 'Unknown Error')}")
                        return

        name = d.get('PlayerNickname', 'Unknown')
        before = d.get('LikesbeforeCommand', '0')
        after = d.get('LikesafterCommand', '0')
        given_by_api = int(d.get('LikesGivenByAPI', 0))

        # Check for Wrong UID (if name is missing or unknown)
        if name == 'Unknown' or not name:
            await wait_msg.edit_text("❌ Wrong Player UID")
            return

        # CLAIMED LOGIC: If no likes were added, show Claimed
        if given_by_api == 0:
            given = "Claimed"
        else:
            given = f"+{given_by_api}"

        # Dynamic User Name & Dynamic Likes 
        final_box = (
            f"ㅤㅤㅤ!! ʜᴇʏ {caller_name.upper()} !!\n"
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
        await wait_msg.edit_text("❌ Wrong Player UID or Server Down")

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
    if await is_admin(u.effective_user):
        wait = await u.effective_chat.send_message("🔍 ᴄʜᴇᴄᴋɪɴɢ...")
        try:
            g = Github(G_TOKEN)
            g.get_repo(REPO_NAME)
            await wait.edit_text("✅ **Connected!**\nRepo: `OB53`\nBot Status: Active")
        except Exception as e:
            await wait.edit_text(f"❌ Connection Error: {e}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# --- MAIN CORE RUNNER ---
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def main_runner():
    print("--> [SYSTEM] Initializing GT BOT Engine...")
    application = ApplicationBuilder().token(B_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("like", like_cmd))
    application.add_handler(CommandHandler("update", update_trigger))
    application.add_handler(CommandHandler("check", check_sys))
    application.add_handler(MessageHandler(filters.Document.ALL, file_handler))
    
    asyncio.create_task(auto_refresh_engine(application))
    
    async with application:
        await application.initialize()
        await application.start()
        print("--> [SYSTEM] Bot is Live and Polling.")
        await application.updater.start_polling(drop_pending_updates=True)
        stop_event = asyncio.Event()
        await stop_event.wait()

if __name__ == "__main__":
    flask_thread = Thread(target=run_flask_server, daemon=True)
    flask_thread.start()
    
    try:
        asyncio.run(main_runner())
    except (KeyboardInterrupt, SystemExit):
        print("--> [SYSTEM] Shutdown Signal Received.")
