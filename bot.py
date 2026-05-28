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

def load_lock_state():
    """Loads locked state from local lock_state.json"""
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading lock state: {e}")
            return {"locked_until": None}
    return {"locked_until": None}

def save_lock_state(locked_until_iso):
    """Saves locked state to local lock_state.json"""
    try:
        with open(LOCK_FILE, "w") as f:
            json.dump({"locked_until": locked_until_iso}, f, indent=4)
    except Exception as e:
        print(f"Error saving lock state: {e}")

def parse_duration(time_str):
    """Parses time strings like '4h', '30m', '1d' and returns a timedelta."""
    match = re.match(r'^(\d+)\s*([a-zA-Z]+)$', time_str.strip())
    if not match:
        return None
    amount = int(match.group(1))
    unit = match.group(2).lower()
    if unit in ['m', 'min', 'minute', 'minutes']:
        return datetime.timedelta(minutes=amount)
    elif unit in ['h', 'hr', 'hour', 'hours']:
        return datetime.timedelta(hours=amount)
    elif unit in ['d', 'day', 'days']:
        return datetime.timedelta(days=amount)
    elif unit in ['s', 'sec', 'second', 'seconds']:
        return datetime.timedelta(seconds=amount)
    return None

def get_current_ist():
    """Gets current Indian Standard Time (IST = UTC + 5:30)"""
    utc_now = datetime.datetime.now(datetime.timezone.utc)
    ist_offset = datetime.timedelta(hours=5, minutes=30)
    return utc_now + ist_offset

def get_current_cycle_start(dt_ist):
    """Returns the start datetime of the current 4 AM - 4 AM IST daily cycle"""
    if dt_ist.hour < 4:
        cycle_date = (dt_ist - datetime.timedelta(days=1)).date()
    else:
        cycle_date = dt_ist.date()
    return datetime.datetime.combine(cycle_date, datetime.time(4, 0))

def get_next_reset_time_ist(dt_ist):
    """Returns the exact datetime of the upcoming 4:00 AM IST reset"""
    if dt_ist.hour < 4:
        return datetime.datetime.combine(dt_ist.date(), datetime.time(4, 0))
    else:
        return datetime.datetime.combine(dt_ist.date() + datetime.timedelta(days=1), datetime.time(4, 0))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# --- GLOBAL CHAT & STATE MANAGEMENT ---
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def global_handler(u: Update, c: ContextTypes.DEFAULT_TYPE):
    """Handles anti-link in groups and private access control as per old code"""
    if not u.message: return

    user_id = u.effective_user.id
    chat_id = u.effective_chat.id
    text = u.message.text.strip() if u.message and u.message.text else ""

    # Check custom user state in chat_data
    active_custom = c.chat_data.get("active_custom")
    if active_custom:
        expected_user = active_custom.get("user_id")
        state = active_custom.get("state")
        
        # If any other user sends a message while this session is active, ignore their message!
        if user_id != expected_user:
            return

        if state == "AWAITING_UID":
            if not text.isdigit():
                await u.effective_chat.send_message("❌ Invalid FF ID! Please enter numbers only.")
                c.chat_data.pop("active_custom", None)
                return
            active_custom["temp_uid"] = text
            active_custom["state"] = "AWAITING_REGION"
            await u.effective_chat.send_message("REGION (example:- ind, bd, etc)")
            return

        elif state == "AWAITING_REGION":
            reg = text.lower()
            uid = active_custom.get("temp_uid")
            
            # Save auto-like
            idx, auto_time_str, day_status = add_or_update_auto_like(user_id, uid, reg, 1)
            
            now_ist = get_current_ist()
            if now_ist.hour < 9:
                day_text = "आज"
            else:
                day_text = "कल"
                
            first_name = active_custom.get("first_name", u.effective_user.first_name)
            success_msg = (
                f"congratulation {first_name}\n"
                f"Auto like added ✅\n"
                f"FF id:-{uid}\n"
                f"region:- {reg}\n"
                f"Day:- {day_status}\n"
                f"आपको {day_text} {auto_time_str} में लाइक मिल जाएगा।"
            )
            await u.effective_chat.send_message(success_msg)
            
            # Clear state
            c.chat_data.pop("active_custom", None)
            return

    # Check admin/owner custom state
    admin_state = c.user_data.get("admin_uid_state")
    if admin_state == "AWAITING_ADMIN_PARAMS":
        expected_user = c.user_data.get("admin_user_id")
        expected_chat = c.user_data.get("admin_chat_id")
        if expected_user is not None and expected_chat is not None:
            if user_id != expected_user or chat_id != expected_chat:
                return

        parts = text.split()
        if len(parts) < 2:
            await u.effective_chat.send_message("❌ Invalid format! Enter region, uid, day (example: ind 123456789 7)")
            c.user_data.pop("admin_uid_state", None)
            return
            
        reg = parts[0].lower()
        uid = parts[1]
        try:
            day = int(parts[2]) if len(parts) > 2 else 7
        except:
            day = 7
            
        # Add to auto target (as admin - multiple allowed)
        idx, auto_time_str, day_status = add_or_update_auto_like(user_id, uid, reg, day, added_by_admin=True)
        
        caller_name = u.effective_user.first_name.upper()
        success_msg = (
            f"congratulation {caller_name}\n"
            f"✅ Auto like added\n"
            f"FF id:- {uid}\n"
            f"region:- {reg}\n"
            f"Day:- {day_status}"
        )
        await u.effective_chat.send_message(success_msg)
        
        # Clear admin state
        c.user_data.pop("admin_uid_state", None)
        c.user_data.pop("admin_chat_id", None)
        c.user_data.pop("admin_user_id", None)
        return

    # Intercept to catch admin reply for /off lock time
    if await is_admin(u.effective_user) and c.user_data.get("awaiting_lock_time"):
        c.user_data["awaiting_lock_time"] = False
        time_str = u.message.text.strip()
        await process_lock_time(u, c, time_str)
        return

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
            
        # ─── DAILY 8:00 AM GUEST.JSON TRACKING & UPDATE ───
        try:
            now_ist = get_current_ist()
            today_date_str = now_ist.date().isoformat()
            
            last_update_date = None
            if os.path.exists("guest_last_update.json"):
                try:
                    with open("guest_last_update.json", "r") as f:
                        meta = json.load(f)
                        last_update_date = meta.get("last_update_date")
                except:
                    pass
            
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
                    if cred_file_name == "guest.json":
                        bot_msg = f"guest file se id pass lekar {updated_count} token update huaa"
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
    """Adds or updates user auto likes target queue"""
    targets = []
    if os.path.exists("auto_uids.json"):
        try:
            with open("auto_uids.json", "r") as f:
                targets = json.load(f)
        except Exception as e:
            print(f"Error reading auto_uids.json: {e}")
            targets = []

    if not added_by_admin:
        updated_targets = []
        for t in targets:
            if str(t.get("user_id")) != str(user_id):
                updated_targets.append(t)
        targets = updated_targets

    new_entry = {
        "uid": str(uid).strip(),
        "region": str(region).strip().lower(),
        "day": int(day),
        "user_id": str(user_id),
        "added_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    targets.append(new_entry)

    try:
        with open("auto_uids.json", "w") as f:
            json.dump(targets, f, indent=4)
    except Exception as e:
        print(f"Error writing to auto_uids.json: {e}")

    idx = len(targets) - 1
    start_hour = 9
    total_minutes = idx
    target_hour = start_hour + (total_minutes // 60)
    target_minute = total_minutes % 60
    am_pm = "AM" if target_hour < 12 else "PM"
    display_hour = target_hour % 12
    if display_hour == 0:
        display_hour = 12
    auto_time_str = f"{display_hour:02d}:{target_minute:02d} {am_pm}"

    return idx, auto_time_str, day


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# --- DAILY AUTO LIKE ENGINE ---
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def daily_auto_like_engine(application):
    print("--> [SYSTEM] Daily Auto Like Engine Started (Target: 09:00 AM IST).")
    while True:
        now_utc = datetime.datetime.utcnow()
        now_ist = now_utc + datetime.timedelta(hours=5, minutes=30)
        
        if now_ist.hour == 9 and now_ist.minute == 0:
            print("--> [AUTO LIKE] Time is 09:00 AM IST. Running daily likes in queue...")
            try:
                if os.path.exists("auto_uids.json"):
                    with open("auto_uids.json", "r") as f:
                        targets = json.load(f)
                    
                    if targets:
                        for idx, target in enumerate(targets):
                            reg = target.get("region", "ind").lower()
                            uid = target.get("uid")
                            if not uid: continue
                            
                            print(f"--> [AUTO LIKE QUEUE] Processing {uid} ({reg}) at position {idx}...")
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
                                                    msg_header = "<span>ꜱᴜᴄᴄᴇssꜰᴜʟʟʏ ʟɪᴋᴇ ꜱᴇɴᴛ</span>"

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
                                                await application.bot.send_message(chat_id=GRP_ID, text=final_box)
                            except Exception as inner_e:
                                print(f"--> [AUTO LIKE API ERROR] UID {uid}: {inner_e}")
                            
                            day_left = target.get("day", 1) - 1
                            target["day"] = day_left
                            
                            try:
                                with open("auto_uids.json", "w") as f_save:
                                    json.dump(targets, f_save, indent=4)
                            except Exception as save_err:
                                print(f"Error saving updated auto target: {save_err}")
                            
                            await asyncio.sleep(60)

                        remaining_targets = [t for t in targets if t.get("day", 0) > 0]
                        try:
                            with open("auto_uids.json", "w") as f_cleanup:
                                json.dump(remaining_targets, f_cleanup, indent=4)
                        except Exception as wrap_err:
                             print(f"Error cleaning up auto targets: {wrap_err}")
                else:
                    print("--> [AUTO LIKE] auto_uids.json not found!")
            except Exception as e:
                print(f"--> [AUTO LIKE ERROR] {e}")
            
            await asyncio.sleep(61)
        else:
            await asyncio.sleep(30)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# --- COMMAND HANDLERS ---
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def start_cmd(u: Update, c: ContextTypes.DEFAULT_TYPE):
    name = sc(u.effective_user.first_name)
    welcome_text = (
        f"!! ʜᴇʏ {name} !!\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "ᴏᴡɴᴇʀ: @ankitraj444\n"
        "sᴛᴀᴛᴜs: ᴏɴʟɪɴᴇ ✅\n\n"
        "📜 ᴄᴏᴍᴍᴀɴᴅs:\n"
        "➥ /like [ʀᴇɢɪᴏɴ] [ᴜɪᴅ]\n"
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

async def off_cmd(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(u.effective_user): return
    
    if c.args:
        time_str = c.args[0]
        await process_lock_time(u, c, time_str)
        return
        
    c.user_data["awaiting_lock_time"] = True
    await u.effective_chat.send_message("Enter your time to open")

async def process_lock_time(u: Update, c: ContextTypes.DEFAULT_TYPE, time_str: str):
    duration = parse_duration(time_str)
    if not duration:
        await u.effective_chat.send_message("❌ Invalid format! Please use format like: 4h, 30m, 1d")
        return
        
    now_ist = get_current_ist()
    locked_until_ist = now_ist + duration
    
    save_lock_state(locked_until_ist.replace(tzinfo=None).isoformat())
    
    raw_str = locked_until_ist.strftime("%I:%M %p").lstrip('0').replace(" ", "")
    if ":00" in raw_str:
        raw_str = raw_str.replace(":00", "")
    end_time_str = raw_str
    
    await u.effective_chat.send_message("✅ Done")
    
    group_msg = f"⚠️ Ab sab /like command {end_time_str} me use kar paoge."
    try:
        await c.bot.send_message(chat_id=GRP_ID, text=group_msg)
    except Exception as e:
        print(f"Error broadcasting to group GRP_ID: {e}")

async def button_callback_handler(u: Update, c: ContextTypes.DEFAULT_TYPE):
    query = u.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    first_name = query.from_user.first_name
    
    if data.startswith("set_auto:"):
        parts = data.split(":")
        reg = parts[1]
        uid = parts[2]
        
        idx, auto_time_str, day_status = add_or_update_auto_like(user_id, uid, reg, 1)
        
        now_ist = get_current_ist()
        if now_ist.hour < 9:
            day_text = "आज"
        else:
            day_text = "कल"
            
        success_msg = (
            f"congratulation {first_name}\n"
            f"Auto like added ✅\n"
            f"FF id:-{uid}\n"
            f"region:- {reg}\n"
            f"Day:- 1\n"
            f"आपको {day_text} {auto_time_str} में लाइक मिल जाएगा।"
        )
        await query.message.edit_text(success_msg)
        
    elif data == "customize_flow":
        c.chat_data["active_custom"] = {
            "user_id": user_id,
            "state": "AWAITING_UID",
            "first_name": first_name
        }
        await query.message.reply_text("ENTER YOUR FF ID")


async def autolike_cmd(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(u.effective_user): return
    
    c.user_data["admin_uid_state"] = "AWAITING_ADMIN_PARAMS"
    c.user_data["admin_chat_id"] = u.effective_chat.id
    c.user_data["admin_user_id"] = u.effective_user.id
    
    await u.effective_chat.send_message("ENTER YOUR REGION, UID, DAY")


async def like_cmd(u: Update, c: ContextTypes.DEFAULT_TYPE):
    is_user_admin = await is_admin(u.effective_user)
    limit_display = "Admin"
    
    if not is_user_admin:
        # Check global /off lock state
        lock_state = load_lock_state()
        locked_until_str = lock_state.get("locked_until")
        if locked_until_str:
            try:
                locked_until_dt = datetime.datetime.fromisoformat(locked_until_str)
                now_ist_naive = get_current_ist().replace(tzinfo=None)
                if now_ist_naive < locked_until_dt:
                    raw_str = locked_until_dt.strftime("%I:%M %p").lstrip('0').replace(" ", "")
                    if ":00" in raw_str:
                        raw_str = raw_str.replace(":00", "")
                    end_time_str = raw_str
                    
                    lock_msg = f"❌ /like command locked hai. Aap ise {end_time_str} se use kar paoge."
                    await u.effective_chat.send_message(lock_msg)
                    return
            except Exception as e:
                print(f"Error checking lock state in like_cmd: {e}")

        # Check 9 AM - 11 AM IST daily window
        now_ist = get_current_ist()
        current_time = now_ist.time()
        allowed_start = datetime.time(9, 0)
        allowed_end = datetime.time(11, 0)
        
        if not (allowed_start <= current_time <= allowed_end):
            time_msg = (
                "माफ़ करें।\n"
                "डेली सुबह 9 बजे से लेकर दोपहर 11 बजे के अंदर ही लाइक ले पाओगे। \n"
                "You will be able to get likes only between 9 am to 11 am daily."
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

        user_id = str(u.effective_user.id)
        cycle_start = get_current_cycle_start(now_ist)
        
        limits_data = load_user_limits()
        user_history = limits_data.get(user_id, [])
        
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
        limits_data[user_id] = current_cycle_uses
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
        print("--> [SYSTEM] Keeping Flask server alive so you can set BOT_TOKEN.")
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
        asyncio.create_task(daily_auto_like_engine(application))
        
        async with application:
            await application.initialize()
            await application.start()
            print("--> [SYSTEM] Bot is Live with Full Security and Auto-Refresh.")
            try:
                await application.bot.delete_webhook(drop_pending_updates=True)
                print("--> [SYSTEM] Webhook deleted successfully to clear past conflicts.")
            except Exception as e:
                print(f"--> [SYSTEM] Webhook deletion skipped: {e}")
            await application.updater.start_polling(drop_pending_updates=True)
            await asyncio.Event().wait()
    except Exception as e:
        print(f"--> [CRITICAL ERROR] Bot failed to start: {e}")
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
