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
from flask import Flask
from threading import Thread
from github import Github
from telegram import Update
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
# --- SMART TOKEN VERIFIER ---
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def verify_token_working(token):
    """Checks if the token is ACTUALLY working on Garena Servers (Not just JWT expiry)"""
    url = "https://client.ind.freefiremobile.com/GetPlayerPersonalShow"
    headers = {
        'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)",
        'Authorization': f"Bearer {token}",
        'Content-Type': "application/x-www-form-urlencoded",
        'X-Unity-Version': "2018.4.11f1"
    }
    try:
        async with aiohttp.ClientSession() as session:
            # Sending dummy data. If token is completely dead, server returns 401.
            async with session.post(url, data=b"dummy_check", headers=headers, timeout=5) as r:
                if r.status in [401, 403]:
                    return False # Token is Dead
                return True # Token is Alive (200 OK or 400 Bad Request means Auth passed)
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
    await asyncio.sleep(10) # Startup delay
    
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

            # Backup sync: Make sure tokens list length matches uidpass list length
            if len(tokens) != len(u_data):
                tokens = [{"token": ""} for _ in range(len(u_data))]

            updated_count = 0
            needs_push = False

            print("--> [AUTO] Scanning all tokens for health...")
            async with aiohttp.ClientSession() as session:
                for i, acc in enumerate(u_data):
                    if not AUTO_UPDATE_ACTIVE: break # Stop immediately if kill switch hit
                    
                    current_token = tokens[i].get("token", "")
                    
                    is_expired = True
                    is_working = False
                    
                    if current_token:
                        # 1. Check logical Expiry (JWT)
                        try:
                            payload = jwt.decode(current_token, options={"verify_signature": False})
                            exp = payload.get('exp', 0)
                            if exp > (time.time() + 600):
                                is_expired = False
                        except:
                            pass
                        
                        # 2. Check Physical Working Status (Only if logically alive)
                        if not is_expired:
                            is_working = await verify_token_working(current_token)

                    # 3. Decision to Replace specific token
                    if is_expired or not is_working:
                        print(f"--> [AUTO] Token {i+1} is dead. Fetching new...")
                        api_url = f"{JWT_API_URL}?uid={acc['uid']}&password={acc['password']}"
                        async with session.get(api_url) as r:
                            if r.status == 200:
                                res = await r.json()
                                new_token = res.get("token")
                                if new_token:
                                    tokens[i] = {"token": new_token}
                                    updated_count += 1
                                    needs_push = True

            # Push only if there was an update
            if needs_push and AUTO_UPDATE_ACTIVE:
                if await github_push(tokens, f"Smart Update: Replaced {updated_count} bad tokens"):
                    await application.bot.send_message(
                        chat_id=ADMIN_ID, 
                        text=f"🔄 **Auto Update Alert**\n{updated_count} dead/expired tokens have been replaced successfully."
                    )
                
        except Exception as e:
            print(f"--> [AUTO LOOP ERROR] {e}")
            
        # 8 Minutes Wait Loop (Interruptible)
        for _ in range(480):
            if not AUTO_UPDATE_ACTIVE: break
            await asyncio.sleep(1)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# --- COMMAND HANDLERS ---
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
            "➥ /status - ᴄʜᴇᴄᴋ ᴛᴏᴋᴇɴs ʜᴇᴀʟᴛʜ\n"
            "➥ /stop1490 - ᴋɪʟʟ ᴀᴜᴛᴏ ᴜᴘᴅᴀᴛᴇ\n"
            "➥ /start1490 - ʀᴇsᴜᴍᴇ ᴀᴜᴛᴏ ᴜᴘᴅᴀᴛᴇ\n"
            "━━━━━━━━━━━━━━━━━━━━"
        )
        await u.effective_chat.send_message(welcome_text)

async def status_cmd(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(u.effective_user): return
    
    wait_msg = await u.effective_chat.send_message("🔍 **Scanning Tokens Health. Please wait...**")
    
    try:
        g = Github(G_TOKEN)
        repo = g.get_repo(REPO_NAME)
        t_file = repo.get_contents("tokens.json")
        tokens = json.loads(t_file.decoded_content.decode())
        
        total = len(tokens)
        working = 0
        dead = 0
        
        # Check last update from the first token's issue time
        last_updated = "Unknown"
        if total > 0 and tokens[0].get("token"):
            try:
                payload = jwt.decode(tokens[0]["token"], options={"verify_signature": False})
                last_updated = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(payload.get('iat', 0)))
            except: pass

        for t_dict in tokens:
            t = t_dict.get("token", "")
            if not t:
                dead += 1
                continue
            
            # Fast check
            if await verify_token_working(t):
                working += 1
            else:
                dead += 1
                
        loop_state = "ACTIVE 🟢" if AUTO_UPDATE_ACTIVE else "STOPPED 🔴"
        
        report = (
            f"📊 **API STATUS REPORT** 📊\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📝 **Total Tokens :** {total}\n"
            f"✅ **Working/Live :** {working}\n"
            f"❌ **Dead/Expired :** {dead}\n"
            f"🕒 **Last Updated :** {last_updated}\n"
            f"⚙️ **Auto-Update  :** {loop_state}\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        await wait_msg.edit_text(report)
        
    except Exception as e:
        await wait_msg.edit_text(f"❌ Status check failed: {e}")

async def stop_auto(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(u.effective_user): return
    global AUTO_UPDATE_ACTIVE
    AUTO_UPDATE_ACTIVE = False
    await u.effective_chat.send_message("🛑 **EMERGENCY STOP:** Auto-update loop has been PAUSED.")

async def start_auto(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(u.effective_user): return
    global AUTO_UPDATE_ACTIVE
    AUTO_UPDATE_ACTIVE = True
    await u.effective_chat.send_message("🟢 **RESUMED:** Auto-update loop is now ACTIVE.")

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

        if name == 'Unknown' or not name:
            await wait_msg.edit_text("❌ Wrong Player UID")
            return

        if given_by_api == 0:
            given = "0 (Daily Limit Reached/Already Liked)"
            msg_header = "⚠️ ʟɪᴍɪᴛ ʀᴇᴀᴄʜᴇᴅ ᴏʀ ᴀʟʀᴇᴀᴅʏ ʟɪᴋᴇᴅ"
        else:
            given = f"+{given_by_api}"
            msg_header = "ꜱᴜᴄᴄᴇssꜰᴜʟʟʏ ʟɪᴋᴇ ꜱᴇɴᴛ"

        final_box = (
            f"ㅤㅤㅤ!! ʜᴇʏ {caller_name.upper()} !!\n"
            f"✪━━━━━━━━━━━━━━━✪\n"
            f"╭💝\n"
            f"│{msg_header}\n"
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


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# --- MAIN CORE RUNNER ---
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def main_runner():
    print("--> [SYSTEM] Initializing GT BOT Engine...")
    application = ApplicationBuilder().token(B_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("like", like_cmd))
    application.add_handler(CommandHandler("status", status_cmd))
    application.add_handler(CommandHandler("stop1490", stop_auto))
    application.add_handler(CommandHandler("start1490", start_auto))
    
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
