# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GT BOT - FULL HEAVY VERSION (PRIVATE REPO MODE)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import aiohttp
import os
import asyncio
import json
import time
import logging
import jwt  
import re
from flask import Flask
from threading import Thread
from github import Github
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- GLOBAL KILL SWITCH ---
AUTO_UPDATE_ACTIVE = True

app = Flask('')

@app.route('/')
def home():
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

B_TOKEN = os.environ.get("BOT_TOKEN")
G_TOKEN = os.environ.get("G_TOKEN")
ADMIN_ID = str(os.environ.get("ADMIN_ID", ""))
REPO_NAME = "jjppjjpp0099-ux/OB53like-api" 
JWT_API_URL = "https://xtytdtyj-jwt.up.railway.app/token"
LIKE_API = "https://ob-53like-api.vercel.app/like"
GRP_ID = -1002316321534

def sc(t):
    normal = "abcdefghijklmnopqrstuvwxyz0123456789"
    fancy = "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ0123456789"
    return str(t).lower().translate(str.maketrans(normal, fancy))

async def is_admin(u):
    if not u: return False
    return str(u.id) == ADMIN_ID or u.username == "ankitraj444"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# --- PRIVATE ACCESS & ANTI-LINK LOGIC ---
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def global_handler(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if not u.message: return

    # 1. ANTI-LINK LOGIC (FOR GROUP)
    if u.effective_chat.id == GRP_ID:
        if not await is_admin(u.effective_user):
            # Check for links in text or caption
            text = u.message.text or u.message.caption or ""
            urls = re.findall(r'(https?://\S+|t\.me/\S+|www\.\S+)', text)
            if urls:
                try:
                    await u.message.delete()
                    return # Stop processing further
                except Exception as e:
                    print(f"Error deleting link: {e}")

    # 2. PRIVATE BOT LOGIC (FOR DM)
    if u.effective_chat.type == "private":
        if not await is_admin(u.effective_user):
            keyboard = [
                [InlineKeyboardButton("👤 DM OWNER", url="https://t.me/ankitraj444")],
                [InlineKeyboardButton("📢 JOIN GROUP", url="https://t.me/ankitraj4444")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await u.message.reply_text(
                "Bot is private, use only official group 👇",
                reply_markup=reply_markup
            )
            return # Don't process other commands if unauthorized

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# --- SMART TOKEN VERIFIER ---
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def verify_token_working(token):
    url = "https://client.ind.freefiremobile.com/GetPlayerPersonalShow"
    headers = {
        'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)",
        'Authorization': f"Bearer {token}",
        'Content-Type': "application/x-www-form-urlencoded",
        'X-Unity-Version': "2018.4.11f1"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=b"dummy_check", headers=headers, timeout=5) as r:
                if r.status in [401, 403]:
                    return False 
                return True 
    except:
        return False

async def github_push(content, commit_msg):
    try:
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
# --- BACKGROUND 8-MINUTES ENGINE ---
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def auto_refresh_engine(application):
    global AUTO_UPDATE_ACTIVE
    print("-->[SYSTEM] Smart Background Auto-Refresh Engine Started (8 Min Cycle).")
    await asyncio.sleep(10) 
    
    while True:
        if not AUTO_UPDATE_ACTIVE:
            await asyncio.sleep(10)
            continue
            
        try:
            g = Github(G_TOKEN)
            repo = g.get_repo(REPO_NAME)
            
            try:
                t_file = repo.get_contents("tokens.json")
                tokens = json.loads(t_file.decoded_content.decode())
            except:
                tokens =[]

            try:
                u_file = repo.get_contents("uidpass.json")
                u_data = json.loads(u_file.decoded_content.decode())
            except:
                u_data =[]

            if len(tokens) != len(u_data):
                tokens = [{"token": ""} for _ in range(len(u_data))]

            updated_count = 0
            needs_push = False

            async with aiohttp.ClientSession() as session:
                for i, acc in enumerate(u_data):
                    if not AUTO_UPDATE_ACTIVE: break
                    
                    current_token = tokens[i].get("token", "")
                    is_expired = True
                    is_working = False
                    
                    if current_token:
                        try:
                            payload = jwt.decode(current_token, options={"verify_signature": False})
                            exp = payload.get('exp', 0)
                            if exp > (time.time() + 600):
                                is_expired = False
                        except:
                            pass
                        
                        if not is_expired:
                            is_working = await verify_token_working(current_token)

                    if is_expired or not is_working:
                        api_url = f"{JWT_API_URL}?uid={acc['uid']}&password={acc['password']}"
                        async with session.get(api_url) as r:
                            if r.status == 200:
                                res = await r.json()
                                new_token = res.get("token")
                                if new_token:
                                    tokens[i] = {"token": new_token}
                                    updated_count += 1
                                    needs_push = True

            if needs_push and AUTO_UPDATE_ACTIVE:
                if await github_push(tokens, f"Smart Update: Replaced {updated_count} bad tokens"):
                    await application.bot.send_message(
                        chat_id=ADMIN_ID, 
                        text=f"🔄 **Auto Update Alert**\n{updated_count} dead/expired tokens have been replaced successfully."
                    )
                
        except Exception as e:
            print(f"--> [AUTO LOOP ERROR] {e}")
            
        for _ in range(480):
            if not AUTO_UPDATE_ACTIVE: break
            await asyncio.sleep(1)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# --- COMMAND HANDLERS ---
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def start_cmd(u: Update, c: ContextTypes.DEFAULT_TYPE):
    # Only allowed for Group or Admin
    if u.effective_chat.id == GRP_ID or await is_admin(u.effective_user):
        name = sc(u.effective_user.first_name)
        welcome_text = (
            f"!! ʜᴇʏ {name} !!\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "ᴏᴡɴᴇʀ: @ankitraj444\n"
            "sᴛᴀᴛᴜs: ᴏɴʟɪɴᴇ ✅\n\n"
            "📜 ᴄᴏᴍᴍᴀɴᴅs:\n"
            "➥ /like[ʀᴇɢɪᴏɴ] [ᴜɪᴅ]\n"
            "➥ /status - ᴄʜᴇᴄᴋ ᴛᴏᴋᴇɴs ʜᴇᴀʟᴛʜ\n"
            "➥ /stop1490 - ᴋɪʟʟ ᴀᴜᴛᴏ ᴜᴘᴅᴀᴛᴇ\n"
            "➥ /start1490 - ʀᴇsᴜᴍᴇ ᴀᴜᴛᴏ ᴜᴘᴅᴀᴛᴇ\n"
            "━━━━━━━━━━━━━━━━━━━━"
        )
        await u.effective_chat.send_message(welcome_text)

async def status_cmd(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(u.effective_user): return
    wait_msg = await u.effective_chat.send_message("🔍 **Scanning Tokens...**")
    try:
        g = Github(G_TOKEN)
        repo = g.get_repo(REPO_NAME)
        t_file = repo.get_contents("tokens.json")
        tokens = json.loads(t_file.decoded_content.decode())
        working, dead = 0, 0
        for t_dict in tokens:
            if await verify_token_working(t_dict.get("token", "")): working += 1
            else: dead += 1
        await wait_msg.edit_text(f"📊 **REPORT**\n✅ Live: {working}\n❌ Dead: {dead}")
    except Exception as e:
        await wait_msg.edit_text(f"❌ Error: {e}")

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
                if r.status != 200:
                    await wait_msg.edit_text("❌ Error processing request")
                    return
        await wait_msg.edit_text(f"✅ Likes sent to {uid} ({reg})")
    except:
        await wait_msg.edit_text("❌ API Down")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# --- MAIN CORE RUNNER ---
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def main_runner():
    application = ApplicationBuilder().token(B_TOKEN).build()
    
    # Priority 1: Private check and Anti-Link (Checks every message)
    application.add_handler(MessageHandler(filters.ALL, global_handler), group=-1)
    
    # Priority 2: Standard Commands
    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("like", like_cmd))
    application.add_handler(CommandHandler("status", status_cmd))
    
    asyncio.create_task(auto_refresh_engine(application))
    
    async with application:
        await application.initialize()
        await application.start()
        await application.updater.start_polling(drop_pending_updates=True)
        await asyncio.Event().wait()

if __name__ == "__main__":
    Thread(target=run_flask_server, daemon=True).start()
    asyncio.run(main_runner())
