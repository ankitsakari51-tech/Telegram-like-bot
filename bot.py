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
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- GLOBAL KILL SWITCH ---
AUTO_UPDATE_ACTIVE = True
LIMIT_FILE = "user_limits.json"
LOCK_FILE = "lock_state.json"

app = Flask('')

@app.route('/')
def home():
    bot_token_status = "SET ✅" if os.environ.get("BOT_TOKEN") else "MISSING ❌"
    g_token_status = "SET ✅" if os.environ.get("G_TOKEN") else "MISSING ❌"
    admin_id_status = "SET ✅" if os.environ.get("ADMIN_ID") else "MISSING ❌"
    return {
        "status": "online",
        "bot": "GT BOT",
        "server": "Active",
        "owner": "ankitraj444",
        "BOT_TOKEN": bot_token_status,
        "G_TOKEN": g_token_status,
        "ADMIN_ID": admin_id_status
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
# --- USER LIMIT PERSISTENT ENGINE ---
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def load_user_limits():
    """Loads user limits history from local user_limits.json"""
    if os.path.exists(LIMIT_FILE):
        try:
            with open(LIMIT_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_user_limits(data):
    """Saves user limits history to local user_limits.json"""
    try:
        with open(LIMIT_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error saving user limits: {e}")

def get_current_ist():
    """Returns current datetime in IST timezone"""
    utc_now = datetime.datetime.now(datetime.timezone.utc)
    ist_tz = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    return utc_now.astimezone(ist_tz)

def get_current_cycle_start(now_ist):
    """Gets the beginning of the current reset cycle (04:00 AM IST)"""
    candidate = now_ist.replace(hour=4, minute=0, second=0, microsecond=0)
    if now_ist < candidate:
        candidate -= datetime.timedelta(days=1)
    return candidate.replace(tzinfo=None)

def get_next_reset_time_ist(now_ist):
    """Gets the next occurrence of 04:00 AM IST"""
    candidate = now_ist.replace(hour=4, minute=0, second=0, microsecond=0)
    if now_ist >= candidate:
        candidate += datetime.timedelta(days=1)
    return candidate

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# --- CHANNEL JOIN ENFORCEMENT ENGINE ---
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REQUIRED_CHANNELS = [
    {"username": "@AnkitRaj_FF", "name": "ANᴋɪᴛ Rᴀᴊ ꜰꜰ"},
    {"username": "@FF_LIKES_BOTS", "name": "ꜰꜰ ʟɪᴋᴇꜱ ʙᴏᴛꜱ"}
]

async def check_user_joined_all(bot, user_id):
    """Checks if the user has joined all required channels"""
    for chan in REQUIRED_CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=chan["username"], user_id=int(user_id))
            if member.status in ["left", "kicked"]:
                return False
        except Exception:
            # If bot is not an admin or another telegram issue occurs, fallback to True for safety
            return False
    return True

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# --- VERIFY CHANNELS FLOW HELPER ---
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def get_join_keyboard():
    buttons = []
    for chan in REQUIRED_CHANNELS:
        url = f"https://t.me/{chan['username'].replace('@', '')}"
        buttons.append([InlineKeyboardButton(f"✨ JOIN {chan['name']}", url=url)])
    buttons.append([InlineKeyboardButton("🔄 VERIFY JOIN", callback_data="verify_joined")])
    return InlineKeyboardMarkup(buttons)

async def send_join_request_message(chat, user):
    fancy_name = sc(user.first_name)
    msg = (
        f"🚨 **ᴍᴇᴍʙᴇʀꜱʜɪᴘ ʀᴇǫᴜɪʀᴇᴅ / जॉइन करना अनिवार्य है** 🚨\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👋 ʜᴇʏ {fancy_name},\n\n"
        f"Hamare bot का उपयोग करने के लिए आपको नीचे दिए गए दोनों चैनल्स जॉइन करना होगा।\n\n"
        f"बिना जॉइन किए /like कमांड काम नहीं करेगा। जॉइन करने के बाद **VERIFY JOIN** बटन पर क्लिक करें।\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    await chat.send_message(msg, reply_markup=get_join_keyboard())

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# --- KEY LOCK SYSTEM (ADMIN RE-USE PROTECTION) ---
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def load_lock_state():
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, "r") as f:
                return json.load(f).get("is_locked", False)
        except:
            return False
    return False

def save_lock_state(is_locked):
    try:
        with open(LOCK_FILE, "w") as f:
            json.dump({"is_locked": is_locked}, f)
    except:
        pass

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# --- TOKEN VERIFIER & GITHUB MANAGEMENT ---
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
            
        # ─── DAILY 8:00 AM GUEST.JSON TRACKING & UPDATE ───
        try:
            now_ist = get_current_ist()
            today_date_str = now_ist.date().isoformat()
            
            # Read last update state from local JSON to persist across restarts
            last_update_date = None
            if os.path.exists("guest_last_update.json"):
                try:
                    with open("guest_last_update.json", "r") as f:
                        meta = json.load(f)
                        last_update_date = meta.get("last_update_date")
                except:
                    pass
            
            # Run if it's 8:00 AM IST or after, and we haven't processed today yet
            if now_ist.hour >= 8 and last_update_date != today_date_str:
                print("--> [GUEST AUTO] Triggering daily 8:00 AM Guest.json token generation...")
                g_temp = Github(G_TOKEN)
                repo_temp = g_temp.get_repo(REPO_NAME)
                
                try:
                    g_file = repo_temp.get_contents("guest.json")
                    g_data = json.loads(g_file.decoded_content.decode())
                except Exception as e:
                    print(f"--> [GUEST AUTO] guest.json not found or failed to read: {e}")
                    g_data = None
                
                if g_data:
                    guest_tokens = []
                    updated_guest_count = 0
                    
                    async with aiohttp.ClientSession() as session_temp:
                        for entry in g_data:
                            uid = entry.get("uid")
                            password = entry.get("password")
                            if uid and password:
                                token_val = ""
                                try:
                                    api_url = f"{JWT_API_URL}?uid={uid}&password={password}"
                                    async with session_temp.get(api_url, timeout=10) as r:
                                        if r.status == 200:
                                            res = await r.json()
                                            token_val = res.get("token", "")
                                            if token_val:
                                                updated_guest_count += 1
                                except Exception as inner_err:
                                    print(f"--> [GUEST AUTO] Error fetching token for {uid}: {inner_err}")
                                guest_tokens.append({"token": token_val})
                    
                    if guest_tokens:
                        push_ok = await github_push(guest_tokens, f"Daily execution with guest.json: updated {updated_guest_count} tokens")
                        if push_ok:
                            print(f"--> [GUEST AUTO] Successfully pushed {updated_guest_count} guest tokens to tokens.json.")
                            
                            try:
                                with open("guest_last_update.json", "w") as f_save:
                                    json.dump({"last_update_date": today_date_str}, f_save, indent=4)
                            except Exception as fs_e:
                                print(f"--> [GUEST AUTO] Error saving state: {fs_e}")
                            
                            # Exact telegram alert message requested by user
                            bot_msg = f"guest file se id pass lekar {updated_guest_count} token update huaa"
                            
                            try:
                                await application.bot.send_message(chat_id=GRP_ID, text=bot_msg)
                            except Exception as tg_e:
                                print(f"Error sending guest updates to GRP_ID: {tg_e}")
                                
                            try:
                                if ADMIN_ID:
                                    await application.bot.send_message(chat_id=ADMIN_ID, text=bot_msg)
                            except Exception as tg_adm_e:
                                print(f"Error sending guest updates to Admin: {tg_adm_e}")
                else:
                    print("--> [GUEST AUTO] guest.json is empty or not found on GitHub.")
        except Exception as e:
            print(f"--> [GUEST AUTO EXCEPTION] {e}")

        # ─── REGULAR 8-MINUTE REFRESH CYCLE ───
        try:
            g = Github(G_TOKEN)
            repo = g.get_repo(REPO_NAME)
            
            # Determine if we should use guest.json checking (only before 11:00 AM IST if updated today)
            now_ist = get_current_ist()
            today_date_str = now_ist.date().isoformat()
            has_guest_updated_today = False
            
            if os.path.exists("guest_last_update.json"):
                try:
                    with open("guest_last_update.json", "r") as f:
                        meta = json.load(f)
                        if meta.get("last_update_date") == today_date_str:
                            has_guest_updated_today = True
                except:
                    pass
            
            use_guest = has_guest_updated_today and (now_ist.hour < 11)
            cred_file_name = "guest.json" if use_guest else "uidpass.json"
            
            try:
                t_file = repo.get_contents("tokens.json")
                tokens = json.loads(t_file.decoded_content.decode())
            except:
                tokens = []

            try:
                u_file = repo.get_contents(cred_file_name)
                u_data = json.loads(u_file.decoded_content.decode())
            except Exception as e:
                print(f"--> [AUTO ERROR] Failed to load {cred_file_name}: {e}")
                u_data = []

            if len(tokens) != len(u_data):
                tokens = [{"token": ""} for _ in range(len(u_data))]

            updated_count = 0
            needs_push = False

            print(f"--> [AUTO] Scanning all tokens for health using {cred_file_name} credentials...")
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
                if await github_push(tokens, f"Smart Update: Replaced {updated_count} bad tokens from {cred_file_name}"):
                    await application.bot.send_message(
                        chat_id=ADMIN_ID, 
                        text=f"🔄 **Auto Update Alert**\n{updated_count} dead/expired tokens have been replaced successfully from {cred_file_name}."
                    )
                
        except Exception as e:
            print(f"--> [AUTO LOOP ERROR] {e}")
            
        for _ in range(480):
            if not AUTO_UPDATE_ACTIVE: break
            await asyncio.sleep(1)


def add_or_update_auto_like(user_id, uid, region, day, added_by_admin=False):
    """Adds a new target to auto_uids.json.
    Regular users are limited to exactly 1 active auto-like entry.
    Admin can have unlimited entries.
    Returns: (idx, auto_time_str, day)
    """
    g = Github(G_TOKEN)
    repo = g.get_repo(REPO_NAME)
    
    # Generate static execution time:
    # 1. Take UID and extract some standard numeric digit offset
    clean_uid = "".join(filter(str.isdigit, str(uid)))
    if clean_uid:
        offset_minutes = int(clean_uid) % 480  # Distribute across 8 hours (04:00 AM - 12:00 PM IST)
    else:
        offset_minutes = 0
        
    start_dt = datetime.datetime.now(datetime.timezone.utc).replace(hour=22, minute=30, second=0, microsecond=0) # 4:00 AM IST equivalent in UTC (previous night 22:30)
    exec_dt = start_dt + datetime.timedelta(minutes=offset_minutes)
    
    # Apply Indian formatting standard representation
    ist_exec = exec_dt + datetime.timedelta(hours=5, minutes=30)
    auto_time_str = ist_exec.strftime("%I:%M %p")
    
    try:
        f = repo.get_contents("auto_uids.json")
        data = json.loads(f.decoded_content.decode())
    except:
        data = []
        
    # Remove existing auto-likes for this normal user if they are adding a new one
    if not added_by_admin:
        data = [entry for entry in data if str(entry.get("added_by", "")) != str(user_id)]
        
    # Ensure day is format "Day-1", "Day-2" or "Both"
    if day not in ["Day-1", "Day-2", "Both"]:
        day = "Both"
        
    new_entry = {
        "uid": str(uid),
        "region": str(region).lower(),
        "time": exec_dt.strftime("%H:%M"),
        "exec_time_ist": auto_time_str,
        "day": day,
        "added_by": str(user_id)
    }
    
    data.append(new_entry)
    repo.update_file(f.path, f"Add/Update auto target {uid}", json.dumps(data, indent=4), f.sha)
    return len(data) - 1, auto_time_str, day

def remove_auto_like_by_index(idx):
    """Removes an auto-like target from auto_uids.json by index"""
    g = Github(G_TOKEN)
    repo = g.get_repo(REPO_NAME)
    
    try:
        f = repo.get_contents("auto_uids.json")
        data = json.loads(f.decoded_content.decode())
    except Exception as e:
        print(f"Error loading auto_uids for removal: {e}")
        return False, "Database Empty"
        
    if idx < 0 or idx >= len(data):
        return False, "Invalid ID"
        
    removed = data.pop(idx)
    repo.update_file(f.path, f"Remove auto target {removed.get('uid')}", json.dumps(data, indent=4), f.sha)
    return True, removed.get("uid")

def clear_all_auto_db():
    """Clears all entries inside auto_uids.json"""
    g = Github(G_TOKEN)
    repo = g.get_repo(REPO_NAME)
    try:
        f = repo.get_contents("auto_uids.json")
        repo.update_file(f.path, "Clear all auto databases", "[]", f.sha)
        return True
    except:
        return False

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# --- BACKGROUND DAILY AUTO-LIKE ENGINE ---
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def daily_auto_like_engine(application):
    """Triggers dynamic background auto liking at their scheduled UTC times"""
    print("--> [SYSTEM] Heavy Daily Background Auto-Liker Thread Commenced.")
    await asyncio.sleep(15)
    
    # Persistence key to prevent duplicate triggering within the exact same minute
    last_triggered_minute = ""
    
    while True:
        try:
            now_utc = datetime.datetime.now(datetime.timezone.utc)
            current_time_str = now_utc.strftime("%H:%M") # "HH:MM" represent layout
            
            if current_time_str == last_triggered_minute:
                await asyncio.sleep(5)
                continue
                
            # Connect to github
            g = Github(G_TOKEN)
            repo = g.get_repo(REPO_NAME)
            
            try:
                f_auto = repo.get_contents("auto_uids.json")
                auto_list = json.loads(f_auto.decoded_content.decode())
            except:
                auto_list = []
                
            matched_entries = []
            for entry in auto_list:
                if entry.get("time") == current_time_str:
                    matched_entries.append(entry)
                    
            if matched_entries:
                last_triggered_minute = current_time_str
                print(f"--> [DAILY ENGINE] Time matched {current_time_str}! Executing auto-likes...")
                
                # Load working tokens
                try:
                    f_tokens = repo.get_contents("tokens.json")
                    tokens_data = json.loads(f_tokens.decoded_content.decode())
                except:
                    tokens_data = []
                    
                working_tokens = [t.get("token") for t in tokens_data if t.get("token")]
                
                if not working_tokens:
                    print("--> [DAILY ENGINE] Aborted - No Active Garena Tokens Found.")
                    continue
                    
                async with aiohttp.ClientSession() as session:
                    for target in matched_entries:
                        uid = target.get("uid")
                        region = target.get("region", "ind").lower()
                        added_by = target.get("added_by", "Unknown")
                        
                        success_sent_count = 0
                        
                        # Loop through and hit the Garena servers per token
                        for tok in working_tokens:
                            try:
                                url = "https://client.ind.freefiremobile.com/GetPlayerPersonalShow"
                                headers = {
                                    'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)",
                                    'Authorization': f"Bearer {tok}",
                                    'Content-Type': "application/x-www-form-urlencoded",
                                    'X-Unity-Version': "2018.4.11f1"
                                }
                                # Garena personal show endpoint like pattern payload trigger
                                payload = f"target_offset=0&target_uid={uid}&server_name={region}"
                                async with session.post(url, data=payload, headers=headers, timeout=6) as r:
                                    if r.status == 200:
                                        success_sent_count += 1
                            except Exception as post_e:
                                print(f"Error during execution: {post_e}")
                                
                        msg = (
                            f"🤖 **ᴀᴜᴛᴏ ʟɪᴋᴇ ʀᴇᴘᴏʀᴛ** 🤖\n"
                            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                            f"👤 **ᴘʟᴀʏᴇʀ:** {uid}\n"
                            f"🌍 **ʀᴇɢɪᴏɴ:** {region.upper()}\n"
                            f"🕒 **sᴄʜᴇᴅᴜʟᴇ ᴛɪᴍᴇ:** {target.get('exec_time_ist')}\n"
                            f"💖 **ʟɪᴋᴇꜱ sᴇɴᴛ:** {success_sent_count} / {len(working_tokens)}\n"
                            f"👤 **ᴜsᴇʀ ɪᴅ:** {added_by}\n"
                            f"━━━━━━━━━━━━━━━━━━━━━━━━"
                        )
                        
                        # Send alert
                        try:
                            await application.bot.send_message(chat_id=GRP_ID, text=msg)
                        except Exception as e_grp:
                            print(f"Group dispatch fail: {e_grp}")
                            
                        try:
                            if added_by and added_by != "Unknown" and str(added_by).isdigit():
                                await application.bot.send_message(chat_id=int(added_by), text=msg)
                        except Exception as e_user:
                            print(f"User direct dispatch fail: {e_user}")
                            
        except Exception as err:
            print(f"--> [DAILY CRITICAL LOOP ERROR] {err}")
            
        await asyncio.sleep(10)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# --- BOT COMMAND HANDLERS ---
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def start_cmd(u: Update, c: ContextTypes.DEFAULT_TYPE):
    user_id = u.effective_user.id
    fancy_caller = sc(u.effective_user.first_name)
    
    # 🚨 Force Channel Join Check
    if not await check_user_joined_all(c.bot, user_id):
        await send_join_request_message(u.effective_chat, u.effective_user)
        return
        
    start_msg = (
        f"🙋‍♀️ **WELCOME TO GT LIKES BOT** \n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"👋 **Hello {fancy_caller},**\n\n"
        f"Aap serves aur automatic execution limits pure modern feature control panel ke sath manage kar sakte hain.\n\n"
        f"🚀 **ᴍᴀɪɴ ᴄᴏᴍᴍᴀɴᴅꜱ:**\n"
        f"👍 /like [region] [uid] - Player ko real-time active like bheje.\n"
        f"🤖 /autolike [region] [uid] - Daily automatic target schedule set kare.\n"
        f"📊 /status - Database health aur tokens check kare.\n\n"
        f"✨ **OFFICIAL DEVELOPER:** @ankitraj444"
    )
    await u.effective_chat.send_message(start_msg)


async def stop_auto(u: Update, c: ContextTypes.DEFAULT_TYPE):
    """Admin only bypass function to temporarily pause token scanner background threads"""
    if not await is_admin(u.effective_user):
        await u.effective_chat.send_message("❌ Access Denied: Admin level parameter only.")
        return
    global AUTO_UPDATE_ACTIVE
    AUTO_UPDATE_ACTIVE = False
    await u.effective_chat.send_message("🛑 **Auto Token Updates & Operations Suspended By Admin**")


async def start_auto(u: Update, c: ContextTypes.DEFAULT_TYPE):
    """Admin only bypass to restore active state updates of files"""
    if not await is_admin(u.effective_user):
        await u.effective_chat.send_message("❌ Access Denied.")
        return
    global AUTO_UPDATE_ACTIVE
    AUTO_UPDATE_ACTIVE = True
    await u.effective_chat.send_message("🚀 **Auto Token Updates & Operations Resumed**")


async def off_cmd(u: Update, c: ContextTypes.DEFAULT_TYPE):
    """Temporary lock trigger to stop accept block likes from regular users"""
    if not await is_admin(u.effective_user):
        return
    current_lock = load_lock_state()
    new_lock = not current_lock
    save_lock_state(new_lock)
    
    status_msg = "🔒 **Bot Locked strictly for Users (Admin can still use)**" if new_lock else "🔓 **Bot Unlocked for Everyone**"
    await u.effective_chat.send_message(status_msg)


async def status_cmd(u: Update, c: ContextTypes.DEFAULT_TYPE):
    """Admin only database structure display"""
    if not await is_admin(u.effective_user):
        await u.effective_chat.send_message("❌ Access Denied!")
        return
        
    wait_m = await u.effective_chat.send_message("⏳ Retrieving Database Status Summary...")
    
    try:
        g = Github(G_TOKEN)
        repo = g.get_repo(REPO_NAME)
        
        # Determine if we should use guest.json checking (only before 11:00 AM IST if updated today)
        now_ist = get_current_ist()
        today_date_str = now_ist.date().isoformat()
        has_guest_updated_today = False
        
        if os.path.exists("guest_last_update.json"):
            try:
                with open("guest_last_update.json", "r") as f:
                    meta = json.load(f)
                    if meta.get("last_update_date") == today_date_str:
                        has_guest_updated_today = True
            except:
                pass
        
        use_guest = has_guest_updated_today and (now_ist.hour < 11)
        cred_file_name = "guest.json" if use_guest else "uidpass.json"
        
        try:
            t = repo.get_contents("tokens.json")
            tok_len = len(json.loads(t.decoded_content.decode()))
        except:
            tok_len = 0
            
        try:
            u_f = repo.get_contents("uidpass.json")
            u_len = len(json.loads(u_f.decoded_content.decode()))
        except:
            u_len = 0
            
        try:
            g_f = repo.get_contents("guest.json")
            g_len = len(json.loads(g_f.decoded_content.decode()))
        except:
            g_len = 0
            
        try:
            a_f = repo.get_contents("auto_uids.json")
            a_len = len(json.loads(a_f.decoded_content.decode()))
        except:
            a_len = 0
            
        sys_status = "RUNNING 🟢" if AUTO_UPDATE_ACTIVE else "PAUSED 🔴"
        lock_status = "LOCKED 🔒" if load_lock_state() else "OPEN 🔓"
        guest_today_status = "YES ✅ (8 AM Script Finished)" if has_guest_updated_today else "NO ❌ (Pending/Offline)"
        active_engine = f"guest.json (Before 11:00 AM)" if use_guest else "uidpass.json"
        
        report = (
            f"💻 **ᴀᴅᴍɪɴ ᴄᴏɴᴛʀᴏʟ ᴘᴀɴᴇʟ** 💻\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚙️ **ꜱʏꜱᴛᴇᴍ status:** {sys_status}\n"
            f"🛡️ **ꜱᴇᴄᴜʀɪᴛʏ ɢᴜᴀʀᴅ:** {lock_status}\n"
            f"📂 **ᴀᴄᴛɪᴠᴇ Credentials:** {active_engine}\n\n"
            f"📊 **ᴅᴀᴛᴀʙᴀꜱᴇ metrics:**\n"
            f"🔑 ᴛᴏᴋᴇɴꜱ count: {tok_len}\n"
            f"👤 uɪᴅᴘᴀꜱꜱ IDs: {u_len}\n"
            f"👥 ɢᴜᴇꜱᴛ IDs: {g_len}\n"
            f"🤖 ᴀᴜᴛᴏʟɪᴋᴇ Targets: {a_len}\n\n"
            f"⏰ **ɢᴜᴇꜱᴛ.ᴊꜱᴏɴ Daily Updated:** {guest_today_status}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        await wait_m.edit_text(report)
    except Exception as e:
        await wait_m.edit_text(f"❌ Error connecting: {e}")


async def global_handler(u: Update, c: ContextTypes.DEFAULT_TYPE):
    """Anti-Link / Anti-Spam validator executed daily on all standard updates"""
    if not u.message or not u.message.text: return
    
    # 1. Admin Bypass
    if await is_admin(u.effective_user):
        return
        
    text = u.message.text
    chat_id = u.effective_chat.id
    
    # Check if a link is detected matching standard http structures
    if "t.me" in text or "http" in text or "://" in text:
        try:
            await u.message.delete()
        except:
            pass
        warn = await u.effective_chat.send_message("❌ **Links or advertising are STRICTLY prohibited inside this chat!**")
        await asyncio.sleep(5)
        try:
            await warn.delete()
        except:
            pass


async def button_callback_handler(u: Update, c: ContextTypes.DEFAULT_TYPE):
    """Callback triggers for channel validations"""
    q = u.callback_query
    await q.answer()
    
    user_id = q.from_user.id
    data = q.data
    
    if data == "verify_joined":
        joined = await check_user_joined_all(c.bot, user_id)
        if joined:
            await q.edit_message_text(
                "✅ **Verification Successful / सफलतापूर्वक जॉइन हो गए हैं!**\n\n"
                "Aapka authorization process complete ho gaya hai. Ab aap /like ya /autolike command bejhijhak use kar sakte hain! 🎉"
            )
        else:
            await q.edit_message_text(
                "❌ **Verification Failed / अभी तक आपने जॉइन नहीं किया है!**\n\n"
                "Kripya niche diye gae links se dono channels ko join karein tabhi verify process pass hoga.",
                reply_markup=get_join_keyboard()
            )
            
    elif data.startswith("set_auto:"):
        # Pattern set_auto:{reg}:{uid}
        parts = data.split(":")
        if len(parts) >= 3:
            reg = parts[1]
            uid = parts[2]
            
            # Setup auto databases on active day choice screen
            keyboard = [
                [
                    InlineKeyboardButton("DAY 1 ONLY", callback_data=f"save_auto:Day-1:{reg}:{uid}"),
                    InlineKeyboardButton("DAY 2 ONLY", callback_data=f"save_auto:Day-2:{reg}:{uid}")
                ],
                [
                    InlineKeyboardButton("🔥 BOTH DAYS (RECOMMENDED)", callback_data=f"save_auto:Both:{reg}:{uid}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await q.edit_message_text(
                f"**SELECT ACTIVE AUTOMATION CYCLE:**\n\n"
                f"👤 UID: `{uid}`\n"
                f"🌏 Server: `{reg.upper()}`\n\n"
                f"Aap ye service kis din active chahte hain?",
                reply_markup=reply_markup
            )
            
    elif data.startswith("save_auto:"):
        parts = data.split(":")
        if len(parts) >= 5:
            day = parts[1]
            reg = parts[2]
            uid = parts[3]
            
            try:
                idx, exec_ist, day = add_or_update_auto_like(user_id, uid, reg, day, added_by_admin=False)
                await q.edit_message_text(
                    f"🟢 **ᴀᴜᴛᴏ ʟɪᴋᴇ sᴄʜᴇᴅᴜʟᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ!**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"👤 **ᴘʟᴀʏᴇʀ:** `{uid}`\n"
                    f"🌏 **sᴇʀᴠᴇʀ:** {reg.upper()}\n"
                    f"🕒 **ᴇxᴇᴄᴜᴛɪᴏɴ ᴛɪᴍᴇ (ɪꜱᴛ):** {exec_ist}\n"
                    f"📅 **ᴀᴄᴛɪᴠᴇ ᴅᴀʏ:** {day}\n"
                    f"🆔 **ʀᴇꜰ ID:** `#{idx}`\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"✨ *Daily automatic execution target set on our private server!* ✨"
                )
            except Exception as ex:
                await q.edit_message_text(f"❌ Error updating automatic database: {ex}")
                
    elif data == "customize_flow":
        await q.edit_message_text(
            "🛠️ **Customize Plan / Custom Day Setup:**\n\n"
            "Aap specific schedule customize karne ke liye sidhe static command syntax ka sahara le sakte hain:\n"
            "💬 `Syntax: /autolike [region] [uid] [Day-1/Day-2/Both]`\n\n"
            "Example: `/autolike ind 50607080 Both`"
        )


async def autolike_cmd(u: Update, c: ContextTypes.DEFAULT_TYPE):
    user_id = u.effective_user.id
    
    # 🚨 Force Channel Join Check
    if not await check_user_joined_all(c.bot, user_id):
        await send_join_request_message(u.effective_chat, u.effective_user)
        return
        
    # Check bot level lock state
    is_locked = load_lock_state()
    is_admin_check = await is_admin(u.effective_user)
    
    if is_locked and not is_admin_check:
        await u.effective_chat.send_message("❌ **Database is Locked!** temporary updates blocked by administrator.")
        return
        
    # Command Arguments parsed
    args = c.args
    if len(args) < 2:
        await u.effective_chat.send_message(
            "❌ **Usage / Syntax Error**\n"
            "💬 `Syntax: /autolike [region] [uid] [Day-1/Day-2/Both]`\n"
            "Example: `/autolike ind 12345678 Both`"
        )
        return
        
    reg = args[0].lower()
    uid = args[1]
    
    day = "Both"
    if len(args) >= 3:
        test_day = args[2].strip()
        if test_day in ["Day-1", "Day-2", "Both"]:
            day = test_day
            
    wait_m = await u.effective_chat.send_message("⌛ Scheduling daily database entry...")
    
    try:
        idx, exec_ist, final_day = add_or_update_auto_like(user_id, uid, reg, day, added_by_admin=is_admin_check)
        await wait_m.edit_text(
            f"🟢 **ᴀᴜᴛᴏ ʟɪᴋᴇ sᴄʜᴇᴅᴜʟᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ!**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 **ᴘʟᴀʏᴇʀ:** `{uid}`\n"
            f"🌏 **sᴇʀᴠᴇʀ:** {reg.upper()}\n"
            f"🕒 **ᴇxᴇᴄᴜᴛɪᴏɴ ᴛɪᴍᴇ (ɪꜱᴛ):** {exec_ist}\n"
            f"📅 **ᴀᴄᴛɪᴠᴇ ᴅᴀʏ:** {final_day}\n"
            f"🆔 **ʀᴇꜰ ID:** `#{idx}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✨ *Daily automatic execution target set on our private server!* ✨"
        )
    except Exception as e:
        await wait_m.edit_text(f"❌ Update failure inside active branch: {e}")


async def like_cmd(u: Update, c: ContextTypes.DEFAULT_TYPE):
    user_id = u.effective_user.id
    
    # 🚨 Force Channel Join Check
    if not await check_user_joined_all(c.bot, user_id):
        await send_join_request_message(u.effective_chat, u.effective_user)
        return
        
    # Check lock State and evaluate limits
    is_locked = load_lock_state()
    is_admin_check = await is_admin(u.effective_user)
    
    if is_locked and not is_admin_check:
        await u.effective_chat.send_message("❌ **Bot is temporary locked by safety administrator!**")
        return
        
    now_ist = get_current_ist()
    limit_display = "Unlimited (Admin Bypass)"
    
    if not is_admin_check:
        # Evaluate user times limit system
        # Check current lock state active
        if now_ist.hour >= 4 and now_ist.hour < 8:
            time_msg = (
                "⚠️ **ꜱʏꜱᴛᴇᴍ ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ ᴡɪɴᴅᴏᴡ / 🔔 ꜱᴇᴄᴜʀɪᴛʏ Active**\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "Dosto regular update limit reset check kiya ja rha hai.\n"
                "Aap 04:00 AM IST se lekar 08:00 AM IST tak real-time /like command ka use nahi kar sakte hain.\n"
                "Kripya daily auto-like feature /autolike ka upyog karein is dauran!\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━"
            )
            keyboard = []
            if len(c.args) >= 2:
                reg_arg = c.args[0].lower()
                uid_arg = c.args[1]
                keyboard.append([
                    InlineKeyboardButton("SET AUTO", callback_data=f"set_auto:{reg_arg}:{uid_arg}"),
                    InlineKeyboardButton("COSTOMIZ", callback_data="customize_flow")
                ])
            else:
                keyboard.append([
                    InlineKeyboardButton("COSTOMIZ", callback_data="customize_flow")
                ])
                
            reply_markup = InlineKeyboardMarkup(keyboard)
            await u.effective_chat.send_message(time_msg, reply_markup=reply_markup)
            return

        user_id_str = str(u.effective_user.id)
        cycle_start = get_current_cycle_start(now_ist)
        
        limits_data = load_user_limits()
        user_history = limits_data.get(user_id_str, [])
        
        current_cycle_uses = []
        for ts_str in user_history:
            try:
                ts_dt = datetime.datetime.fromisoformat(ts_str)
                if ts_dt >= cycle_start:
                    current_cycle_uses.append(ts_str)
            except Exception as parse_e:
                pass
        
        if len(current_cycle_uses) >= 2:
            next_reset = get_next_reset_time_ist(now_ist)
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

        if len(c.args) < 2:
            await u.effective_chat.send_message("❌ Usage: /like [region] [uid]")
            return

        current_cycle_uses.append(now_ist.replace(tzinfo=None).isoformat())
        limits_data[user_id_str] = current_cycle_uses
        save_user_limits(limits_data)
        limit_display = f"{len(current_cycle_uses)}/2"

    else:
        if len(c.args) < 2:
            await u.effective_chat.send_message("❌ Usage: /like [region] [uid]")
            return
            
    reg, uid = c.args[0].lower(), c.args[1]
    
    wait_msg = await u.effective_chat.send_message("⌛ ᴘʀᴏᴄᴇssɪɴɢ...")
    caller_name = sc(u.effective_user.first_name)

    try:
        async_likes_url = f"{LIKE_API}?uid={uid}&server_name={reg}"
        async with aiohttp.ClientSession() as ses:
            async with ses.get(async_likes_url) as r:
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
            f"╰━━━━━━━━━━━━━━━✪\n"
            f" Limit: {limit_display}"
        )
        await wait_msg.edit_text(final_box)

    except Exception as e:
        await wait_msg.edit_text("❌ Wrong Player UID or Server Down")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# --- MAIN CORE RUNNER ---
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def main_runner():
    print("--> [SYSTEM] Initializing GT BOT Full Heavy Engine...")
    
    if not B_TOKEN:
        print("--> [CRITICAL ERROR] BOT_TOKEN environment variable is not set! Bot cannot start.")
        print("--> [SYSTEM] Keeping Flask server alive so you can set BOT_TOKEN in your Render dashboard under Environment Variables.")
        while True:
            await asyncio.sleep(3600)
            
    try:
        application = ApplicationBuilder().token(B_TOKEN).build()
        
        # Priority 1: Private check and Anti-Link (Checks every message)
        application.add_handler(MessageHandler(filters.ALL, global_handler), group=-1)
        application.add_handler(CallbackQueryHandler(button_callback_handler))
        
        # Priority 2: Standard Commands
        application.add_handler(CommandHandler("start", start_cmd))
        application.add_handler(CommandHandler("like", like_cmd))
        application.add_handler(CommandHandler("autolike", autolike_cmd))
        application.add_handler(CommandHandler("status", status_cmd))
        application.add_handler(CommandHandler("stop1490", stop_auto))
        application.add_handler(CommandHandler("start1490", start_auto))
        application.add_handler(CommandHandler("off", off_cmd))
        
        asyncio.create_task(auto_refresh_engine(application))
        
        # Start the Daily Auto Like engine in background
        asyncio.create_task(daily_auto_like_engine(application))
        
        async with application:
            await application.initialize()
            await application.start()
            print("--> [SYSTEM] Bot is Live with Full Security and Auto-Refresh.")
            await application.updater.start_polling(drop_pending_updates=True)
            await asyncio.Event().wait()
    except Exception as e:
        print(f"--> [CRITICAL ERROR] Bot failed to start: {e}")
        print("--> [SYSTEM] Keeping Flask server alive so you can update configuration.")
        while True:
            await asyncio.sleep(3600)

def main():
    flask_thread = Thread(target=run_flask_server, daemon=True)
    flask_thread.start()
    
    try:
        asyncio.run(main_runner())
    except (KeyboardInterrupt, SystemExit):
        print("--> [SYSTEM] Shutdown Signal Received.")

if __name__ == "__main__":
    main()
