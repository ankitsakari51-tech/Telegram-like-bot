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
import datetime 
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
LIMIT_FILE = "user_limits.json"

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
# --- USER LIMIT PERSISTENT ENGINE (NEW) ---
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def load_user_limits():
    """Loads user limits history from local user_limits.json"""
    if os.path.exists(LIMIT_FILE):
        try:
            with open(LIMIT_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading limits: {e}")
            return {}
    return {}

def save_user_limits(data):
    """Saves user limits history to local user_limits.json"""
    try:
        with open(LIMIT_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error saving limits: {e}")

def get_current_ist():
    """Gets current Indian Standard Time (IST = UTC + 5:30)"""
    utc_now = datetime.datetime.now(datetime.timezone.utc)
    ist_offset = datetime.timedelta(hours=5, minutes=30)
    return utc_now + ist_offset

def get_current_cycle_start(dt_ist):
    """Returns the start datetime of the current 4 AM - 4 AM IST daily cycle"""
    if dt_ist.hour < 4:
        # If before 4 AM IST, the current cycle started at 4:00 AM yesterday
        cycle_date = (dt_ist - datetime.timedelta(days=1)).date()
    else:
        # If after 4 AM IST, the current cycle started at 4:00 AM today
        cycle_date = dt_ist.date()
    return datetime.datetime.combine(cycle_date, datetime.time(4, 0))

def get_next_reset_time_ist(dt_ist):
    """Returns the exact datetime of the upcoming 4:00 AM IST reset"""
    if dt_ist.hour < 4:
        return datetime.datetime.combine(dt_ist.date(), datetime.time(4, 0))
    else:
        return datetime.datetime.combine(dt_ist.date() + datetime.timedelta(days=1), datetime.time(4, 0))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# --- PRIVATE ACCESS & ANTI-LINK LOGIC (RESTORED) ---
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def global_handler(u: Update, c: ContextTypes.DEFAULT_TYPE):
    """Handles anti-link in groups and private access control as per old code"""
    if not u.message: return

    # 1. ANTI-LINK LOGIC (FOR GROUP)
    if u.effective_chat.id == GRP_ID:
        if not await is_admin(u.effective_user):
            # Check for links in text or caption using regex
            text = u.message.text or u.message.caption or ""
            urls = re.findall(r'(https?://\S+|t\.me/\S+|www\.\S+)', text)
            if urls:
                try:
                    await u.message.delete()
                    return # Stop processing this specific update
                except Exception as e:
                    print(f"Error deleting link: {e}")

    # 2. PRIVATE BOT LOGIC (FOR DM)
    if u.effective_chat.type == "private":
        if not await is_admin(u.effective_user):
            keyboard = [
                [InlineKeyboardButton("DM OWNER", url="https://t.me/ankitraj444")],
                [InlineKeyboardButton("JOIN GROUP", url="https://t.me/ankitraj4444")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await u.message.reply_text(
                "Bot is private, use only official group 👇",
                reply_markup=reply_markup
            )
            return # Block unauthorized DM users from running commands

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# --- SMART TOKEN VERIFIER ---
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def verify_token_working(token):
    """Checks if the token is ACTUALLY working on Garena Servers"""
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
    print("--> [SYSTEM] Smart Background Auto-Refresh Engine Started (8 Min Cycle).")
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
                tokens = []

            try:
                u_file = repo.get_contents("uidpass.json")
                u_data = json.loads(u_file.decoded_content.decode())
            except:
                u_data = []

            if len(tokens) != len(u_data):
                tokens = [{"token": ""} for _ in range(len(u_data))]

            updated_count = 0
            needs_push = False

            print("--> [AUTO] Scanning all tokens for health...")
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
# --- DAILY AUTO LIKE ENGINE ---
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def daily_auto_like_engine(application):
    print("--> [SYSTEM] Daily Auto Like Engine Started (Target: 06:00 AM IST).")
    while True:
        # Get Current IST Time (UTC + 5:30)
        now_utc = datetime.datetime.utcnow()
        now_ist = now_utc + datetime.timedelta(hours=5, minutes=30)
        
        # Check if time is exactly 06:00 AM
        if now_ist.hour == 6 and now_ist.minute == 0:
            print("--> [AUTO LIKE] Time is 06:00 AM IST. Running daily likes...")
            try:
                if os.path.exists("auto_uids.json"):
                    with open("auto_uids.json", "r") as f:
                        targets = json.load(f)
                    
                    for target in targets:
                        reg = target.get("region", "ind").lower()
                        uid = target.get("uid")
                        if not uid: continue
                        
                        try:
                            async with aiohttp.ClientSession() as ses:
                                async with ses.get(f"{LIKE_API}?uid={uid}&server_name={reg}") as r:
                                    if r.status == 200:
                                        d = await r.json()
                                        name = d.get('PlayerNickname', 'Unknown')
                                        before = d.get('LikesbeforeCommand', '0')
                                        after = d.get('LikesafterCommand', '0')
                                        given_by_api = int(d.get('LikesGivenByAPI', 0))
                                        
                                        if name != 'Unknown' and name:
                                            if given_by_api == 0:
                                                given = "0 (Daily Limit Reached/Already Liked)"
                                                msg_header = "ʟɪᴍɪᴛ ʀᴇᴀᴄʜᴇᴅ/ᴀʟʀᴇᴀᴅʏ ʟɪᴋᴇᴅ"
                                            else:
                                                given = f"+{given_by_api}"
                                                msg_header = "ꜱᴜᴄᴄᴇssꜰᴜʟʟʏ ʟɪᴋᴇ ꜱᴇɴᴛ"

                                            final_box = (
                                                f"ㅤㅤㅤ!! 🤖 ᴀᴜᴛᴏ ᴅᴀɪʟʏ ʟɪᴋᴇ 🤖 !!\n"
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
                                            # Send group message 
                                            await application.bot.send_message(chat_id=GRP_ID, text=final_box)
                        except Exception as inner_e:
                            print(f"--> [AUTO LIKE API ERROR] UID {uid}: {inner_e}")
                        
                        await asyncio.sleep(5) # Thoda delay to avoid server spam
                else:
                    print("--> [AUTO LIKE] auto_uids.json not found!")
            except Exception as e:
                print(f"--> [AUTO LIKE ERROR] {e}")
            
            # Sleep for 61 seconds so it doesn't run twice inside 6:00 AM
            await asyncio.sleep(61)
        else:
            # Check time every 30 seconds
            await asyncio.sleep(30)


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
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # --- SMART DAILY LIMIT RATE LIMITER (NEW) ---
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    is_user_admin = await is_admin(u.effective_user)
    
    if not is_user_admin:
        user_id = str(u.effective_user.id)
        now_ist = get_current_ist()
        cycle_start = get_current_cycle_start(now_ist)
        
        limits_data = load_user_limits()
        user_history = limits_data.get(user_id, [])
        
        # Keep only timestamps within the current 4 AM - 4 AM cycle
        current_cycle_uses = []
        for ts_str in user_history:
            try:
                ts_dt = datetime.datetime.fromisoformat(ts_str)
                # Compare naive datetimes (since combine creates naive datetime)
                if ts_dt >= cycle_start:
                    current_cycle_uses.append(ts_str)
            except Exception as parse_e:
                pass
        
        # Verify usage count
        if len(current_cycle_uses) >= 2:
            next_reset = get_next_reset_time_ist(now_ist)
            # Remove UTC / Timezone info for substracting naive datetime
            time_to_wait = next_reset - now_ist.replace(tzinfo=None)
            
            total_seconds = int(time_to_wait.total_seconds())
            hours = max(0, total_seconds // 3600)
            minutes = max(0, (total_seconds % 3600) // 60)
            
            fancy_caller = sc(u.effective_user.first_name)
            block_msg = (
                f"🚫 **ʟɪᴍɪᴛ ʀᴇᴀᴄʜᴇᴅ / 🚨 Sᴇᴄᴜʀɪᴛʏ 🚨**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👋 ʜᴇʏ {fancy_caller},\n\n"
                f"Aapne aaj ki **2 times limit** ko exhaust kar diya hai.\n"
                f"Ab aap naya like sirf agle 4:00 AM IST reset ke baad hi le sakte hain.\n\n"
                f"⏳ **ʀᴇɢᴇɴᴇʀᴀᴛɪᴏɴ ᴛɪᴍᴇ:** {hours}h {minutes}m baaki hai\n"
                f"⏰ **ɴᴇxᴛ ʀᴇsᴇᴛ:** Daily at 04:00 AM IST\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━"
            )
            await u.effective_chat.send_message(block_msg)
            return

        # If not exceeded, record this usage and update JSON metadata
        current_cycle_uses.append(now_ist.replace(tzinfo=None).isoformat())
        limits_data[user_id] = current_cycle_uses
        save_user_limits(limits_data)
        
    # Proceed with native like request handler
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
            msg_header = "ʟɪᴍɪᴛ ʀᴇᴀᴄʜᴇᴅ/ᴀʟʀᴇᴀᴅʏ ʟɪᴋᴇᴅ"
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
    print("--> [SYSTEM] Initializing GT BOT Full Heavy Engine...")
    application = ApplicationBuilder().token(B_TOKEN).build()
    
    # Priority 1: Private check and Anti-Link (Checks every message)
    application.add_handler(MessageHandler(filters.ALL, global_handler), group=-1)
    
    # Priority 2: Standard Commands
    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("like", like_cmd))
    application.add_handler(CommandHandler("status", status_cmd))
    application.add_handler(CommandHandler("stop1490", stop_auto))
    application.add_handler(CommandHandler("start1490", start_auto))
    
    asyncio.create_task(auto_refresh_engine(application))
    
    # Start the Daily Auto Like engine in background
    asyncio.create_task(daily_auto_like_engine(application))
    
    async with application:
        await application.initialize()
        await application.start()
        print("--> [SYSTEM] Bot is Live with Full Security and Auto-Refresh.")
        await application.updater.start_polling(drop_pending_updates=True)
        await asyncio.Event().wait()

if __name__ == "__main__":
    flask_thread = Thread(target=run_flask_server, daemon=True)
    flask_thread.start()
    
    try:
        asyncio.run(main_runner())
    except (KeyboardInterrupt, SystemExit):
        print("--> [SYSTEM] Shutdown Signal Received.")
