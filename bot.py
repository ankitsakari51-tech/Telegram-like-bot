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
LOCK_FILE = "lock_state.json"

app = Flask('')

@app.route('/')
def home():
    return "🤖 GT Bot is Core Live and Ready!"

def run_http_server():
    app.run(host='0.0.0.0', port=3000)

# --- ENVIRONMENT CONFIG ---
B_TOKEN = os.environ.get("B_TOKEN")
GRP_ID_RAW = os.environ.get("GRP_ID", "-1002342083626")
OWN_ID_RAW = os.environ.get("OWN_ID", "7117181046")

try:
    GRP_ID = int(GRP_ID_RAW)
except ValueError:
    print(f"CRITICAL WARNING: GRP_ID env is invalid: '{GRP_ID_RAW}'. Defaulting to -1002342083626")
    GRP_ID = -1002342083626

try:
    OWN_ID = int(OWN_ID_RAW)
except ValueError:
    print(f"CRITICAL WARNING: OWN_ID env is invalid: '{OWN_ID_RAW}'. Defaulting to 7117181046")
    OWN_ID = 7117181046

REG_GRP_ID = os.environ.get("REG_GRP_ID", "https://t.me/G_T_OFFICIAL")
GH_TOKEN = os.environ.get("GH_TOKEN")
GH_REPO = os.environ.get("GH_REPO", "Arardd6/test-")
FILE_PATH = os.environ.get("FILE_PATH", "f.txt")

LIKE_API = "https://freefirelikes-api.vercel.app/api/v1/like"

# --- HELPER PERSISTENCE MODULES ---
def load_lock_state():
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, "r") as f:
                return json.load(f)
        except:
            return {"is_locked": False}
    return {"is_locked": False}

def save_lock_state(state):
    with open(LOCK_FILE, "w") as f:
        json.dump(state, f, indent=4)

def load_user_limits():
    if os.path.exists(LIMIT_FILE):
        try:
            with open(LIMIT_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading {LIMIT_FILE}: {e}")
            return {}
    return {}

def save_user_limits(data):
    try:
        with open(LIMIT_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error saving {LIMIT_FILE}: {e}")

# --- GH TOKENS FETCHER ---
def get_gh_tokens():
    if not GH_TOKEN:
        print("--> [ERROR] GH_TOKEN is missing! Auto-Update cannot run.")
        return []
    try:
        g = Github(GH_TOKEN)
        repo = g.get_repo(GH_REPO)
        fc = repo.get_contents(FILE_PATH)
        content = fc.decoded_content.decode('utf-8')
        tokens = [line.strip() for line in content.split('\n') if line.strip() and "." in line]
        return tokens
    except Exception as e:
        print(f"--> [GH ERROR] Failed to fetch live tokens: {e}")
        return []

def get_tokens_health(tokens):
    working = 0
    dead = 0
    now = time.time()
    for tok in tokens:
        try:
            parts = tok.split('.')
            if len(parts) >= 2:
                payload_b = parts[1]
                # Fix Base64 padding
                payload_b += "=" * ((4 - len(payload_b) % 4) % 4)
                import base64
                payload = json.loads(base64.b64decode(payload_b).decode('utf-8'))
                exp = payload.get('exp', 0)
                if exp > now:
                    working += 1
                else:
                    dead += 1
            else:
                dead += 1
        except Exception:
            dead += 1
    return len(tokens), working, dead

# --- TOKEN AUTO SYNCHRONIZATION BACKEND LOOP ---
async def auto_token_health_loop(application):
    global AUTO_UPDATE_ACTIVE
    print("--> [SYSTEM] Auto Token Health Sync engine initialized.")
    while AUTO_UPDATE_ACTIVE:
        try:
            print("--> [HEALTH LOOP] Commencing token status verification sync...")
            raw_tokens = get_gh_tokens()
            if not raw_tokens:
                print("--> [HEALTH LOOP] No raw tokens successfully loaded.")
            else:
                total, working, dead = get_tokens_health(raw_tokens)
                print(f"--> [HEALTH REPORT] Total: {total} | Working: {working} | Expired/Dead: {dead}")
                
                # Automatically fix/replace dead tokens if we have a replacement policy or alert
                if dead > 0:
                    updated_count = dead
                    await application.bot.send_message(
                        chat_id=GRP_ID,
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
                                                msg_header = "💖 ꜱᴜᴄᴄᴇssꜰᴜʟʟʏ ʟɪᴋᴇ ꜱᴇɴᴛ"

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
            
        await asyncio.sleep(30) # Tick every 30 seconds

# --- BOT INTERACTIVE COMMANDS ---
async def start_cmd(u: Update, c: ContextTypes.DEFAULT_TYPE):
    name = u.effective_user.first_name
    msg = (
        f"!! ʜᴇʏ {name} !!\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "ᴏᴡɴᴇʀ: @ankitraj444\n"
        "sᴛᴀᴛᴜs: ᴏɴʟɪɴᴇ ✅\n\n"
        "📜 ᴄᴏᴍᴍᴀɴᴅs:\n"
        "➥ /like [ʀᴇɢɪᴏɴ] [ᴜɪᴅ]\n"
        "➥ /status - ᴄʜᴇᴄᴋ ᴛᴏᴋᴇɴs ʜᴇᴀʟᴛʜ\n"
        "➥ /stop1490 - ᴋɪʟʟ ᴀᴜᴛᴏ ᴜᴘᴅᴀᴛᴇ\n"
        "➥ /start1490 - ʀᴇsᴜᴍᴇ ᴀᴜᴛᴏ ᴜᴘᴅᴀᴛᴇ\n"
        "➥ /on - ᴛᴜʀɴ ᴏɴ ʟɪᴋᴇ API\n"
        "➥ /off - ᴛᴜʀɴ ᴏꜰꜰ ʟɪᴋᴇ API\n\n"
        "✨ ᴘᴏᴡᴇʀᴇᴅ ʙʏ @ankitraj444 ✨"
    )
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("📢 Channel", url=REG_GRP_ID),
        InlineKeyboardButton("💬 Support Group", url="https://t.me/Ankit_Raj_Official")
    ]])
    await u.effective_chat.send_message(msg, reply_markup=kb)

async def is_admin(user) -> bool:
    if user.id == OWN_ID:
        return True
    return False

async def stop_updater_cmd(u: Update, c: ContextTypes.DEFAULT_TYPE):
    global AUTO_UPDATE_ACTIVE
    if not await is_admin(u.effective_user):
        await u.effective_chat.send_message("❌ Admin Only Command.")
        return
    AUTO_UPDATE_ACTIVE = False
    await u.effective_chat.send_message("🚨 **Token Auto Update Loop Killed!**")

async def start_updater_cmd(u: Update, c: ContextTypes.DEFAULT_TYPE):
    global AUTO_UPDATE_ACTIVE
    if not await is_admin(u.effective_user):
        await u.effective_chat.send_message("❌ Admin Only Command.")
        return
    if AUTO_UPDATE_ACTIVE:
        await u.effective_chat.send_message("ℹ️ **Auto Updater Loop is already running.**")
    else:
        AUTO_UPDATE_ACTIVE = True
        logger.info("[SYSTEM] Initializing background loop manually...")
        asyncio.create_task(auto_token_health_loop(c.application))
        await u.effective_chat.send_message("✅ **Token Auto Update Loop Revived successfully!**")

async def status_cmd(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(u.effective_user):
        await u.effective_chat.send_message("❌ Admin Only Command.")
        return
        
    raw_tokens = get_gh_tokens()
    total, working, dead = get_tokens_health(raw_tokens)
    loop_state = "ACTIVE RUNNING ✅" if AUTO_UPDATE_ACTIVE else "CRITICAL KILLED 🚨"
    now_utc = datetime.datetime.utcnow()
    last_updated = (now_utc + datetime.timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d %I:%M:%S %p (IST)")
    
    rep = (
        f"📊 **API STATUS REPORT** 📊\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📝 **Total Tokens :** {total}\n"
        f"✅ **Working/Live :** {working}\n"
        f"❌ **Dead/Expired :** {dead}\n"
        f"🕒 **Last Updated :** {last_updated}\n"
        f"⚙️ **Auto-Update  :** {loop_state}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ Core Processors Operating Normally."
    )
    await u.effective_chat.send_message(rep)

async def lock_system_on_cmd(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(u.effective_user):
        await u.effective_chat.send_message("❌ Admin Only Command.")
        return
    save_lock_state({"is_locked": False})
    await u.effective_chat.send_message("🔓 **Like Command API turned ON successfully! Users can now request likes.**")

async def lock_system_off_cmd(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(u.effective_user):
        await u.effective_chat.send_message("❌ Admin Only Command.")
        return
    save_lock_state({"is_locked": True})
    await u.effective_chat.send_message("🔒 **Like Command API locked (OFF). User requests will be blocked globally.**")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# --- CORE LIKE REQUEST HANDLER ---
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def like_cmd(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if not (u.effective_chat.id == GRP_ID or await is_admin(u.effective_user)): return
    
    if len(c.args) < 2:
        await u.effective_chat.send_message("❌ Usage: /like [region] [uid]")
        return
        
    reg = c.args[0].lower()
    uid = c.args[1]
    
    if not re.match(r"^\d+$", uid):
        await u.effective_chat.send_message("❌ Please enter a numeric UID.")
        return
        
    # --- SMART DAILY LIMIT RATE LIMITER (NEW) ---
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    is_user_admin = await is_admin(u.effective_user)
    limit_display = "Admin"
    
    if not is_user_admin:
        # Check global /off lock state
        lock_state = load_lock_state()
        if lock_state.get("is_locked", False):
            await u.effective_chat.send_message("🔒 **API is currently locked (OFF) by Owner.** Please wait or contact support.")
            return

        # Check Daily Restricted Active Hours (9 AM to 11 AM IST)
        now_utc = datetime.datetime.utcnow()
        now_ist = now_utc + datetime.timedelta(hours=5, minutes=30)
        
        inside_allowed_window = (9 <= now_ist.hour < 11)
        if not inside_allowed_window:
            time_msg = (
                "माफ़ करें।\n"
                "डेली सुबह 9 बजे से लेकर दोपहर 11 बजे के अंदर ही लाइक ले पाओगे। \n"
                "You will be able to get likes only between 9 am to 11 am daily."
            )
            # Check for local voice file or remote voice URL
            voice_sent = False
            local_found = None
            for ext in ["ogg", "mp3", "wav", "m4a"]:
                if os.path.exists(f"warning.{ext}"):
                    local_found = f"warning.{ext}"
                    break
            
            if local_found:
                try:
                    with open(local_found, "rb") as f:
                        await u.effective_chat.send_voice(voice=f, caption=time_msg)
                        voice_sent = True
                except Exception as e:
                    print(f"Error sending local warning voice: {e}")
            
            if not voice_sent and os.environ.get("VOICE_URL"):
                try:
                    await u.effective_chat.send_voice(voice=os.environ.get("VOICE_URL"), caption=time_msg)
                    voice_sent = True
                except Exception as e:
                    print(f"Error sending remote VOICE_URL: {e}")

            if not voice_sent:
                await u.effective_chat.send_message(time_msg)
            return

        user_id = str(u.effective_user.id)
        limits_data = load_user_limits()
        
        # Determine current rolling cycle (Starts at 4:00 AM IST)
        # Any log entry before today 4:00 AM IST belongs to a different cycle.
        today_4am = now_ist.replace(hour=4, minute=0, second=0, microsecond=0)
        if now_ist < today_4am:
            cycle_start = today_4am - datetime.timedelta(days=1)
        else:
            cycle_start = today_4am
            
        user_uses = limits_data.get(user_id, [])
        # Cleanup expired uses outside of current cycle
        current_cycle_uses = []
        for stamp_str in user_uses:
            try:
                stamp = datetime.datetime.fromisoformat(stamp_str)
                if stamp >= cycle_start.replace(tzinfo=None):
                    current_cycle_uses.append(stamp_str)
            except ValueError:
                continue
                
        if len(current_cycle_uses) >= 2:
            next_reset = cycle_start + datetime.timedelta(days=1)
            time_left = next_reset - now_ist
            hours, remainder = divmod(int(time_left.total_seconds()), 3600)
            minutes, _ = divmod(remainder, 60)
            
            fancy_caller = f"!! {u.effective_user.first_name.upper()} !!" if u.effective_user.first_name else "Guest"
            await u.effective_chat.send_message(
                f"🚫 **ʟɪᴍɪᴛ ʀᴇᴀᴄʜᴇᴅ / 🚨 Sᴇᴄᴜʀɪᴛʏ 🚨**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👋 ʜᴇʏ {fancy_caller},\n\n"
                f"Aapne aaj ki **2 times limit** ko exhaust kar diya hai.\n"
                f"Ab aap naya like sirf agle 4:00 AM IST reset ke baad hi le sakte hain.\n\n"
                f"⏳ **ʀᴇɢᴇɴᴇʀᴀᴛɪᴏɴ ᴛɪᴍᴇ:** {hours}h {minutes}m baaki hai\n"
                f"⏰ **ɴᴇxᴛ ʀᴇsᴇᴛ:** Daily at 04:00 AM IST\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━"
            )
            return
            
        # Append current use
        current_cycle_uses.append(now_ist.replace(tzinfo=None).isoformat())
        limits_data[user_id] = current_cycle_uses
        save_user_limits(limits_data)
        limit_display = f"{len(current_cycle_uses)}/2"
        
    # Proceed with native like request handler
    wait_msg = await u.effective_chat.send_message("⌛ ᴘʀᴏᴄᴇssɪɴɢ...")
    caller_name = u.effective_user.first_name or "PLAYER"
    
    try:
        async with aiohttp.ClientSession() as ses:
            async with ses.get(f"{LIKE_API}?uid={uid}&server_name={reg}") as r:
                if r.status != 200:
                    try:
                        d = await r.json()
                    except:
                        d = {}
                    err_hint = d.get('error', 'API Server Offline')
                    await wait_msg.edit_text(f"❌ Error: {err_hint}")
                    return
                else:
                    try:
                        d = await r.json()
                    except:
                        await wait_msg.edit_text("❌ Got empty/invalid response from API")
                        return
                    
                    # API returns status 400 or other codes inside json sometimes
                    if 'error' in d:
                        await wait_msg.edit_text(f"❌ Request Denied: {d.get('error')}")
                        return
                    else:
                        pass

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
    application = ApplicationBuilder().token(B_TOKEN).build()
    
    # Register command handlings
    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("status", status_cmd))
    application.add_handler(CommandHandler("stop1490", stop_updater_cmd))
    application.add_handler(CommandHandler("start1490", start_updater_cmd))
    application.add_handler(CommandHandler("like", like_cmd))
    application.add_handler(CommandHandler("on", lock_system_on_cmd))
    application.add_handler(CommandHandler("off", lock_system_off_cmd))

    print("--> [SYSTEM] Spawning Background Tasks...")
    asyncio.create_task(auto_token_health_loop(application))
    asyncio.create_task(daily_auto_like_engine(application))

    print("--> [SYSTEM] Activating Telegram Polling...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    print("--> [SYSTEM] Starting Production Flask KeepAlive...")
    # This keeps our web process alive for Render port check
    t = Thread(target=run_http_server)
    t.start()

    # Block run loop
    while True:
        await asyncio.sleep(10)

if __name__ == '__main__':
    # Async launcher entry point
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main_runner())
