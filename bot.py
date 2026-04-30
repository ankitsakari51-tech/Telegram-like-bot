import aiohttp, os, asyncio, json, time, sys
from flask import Flask
from threading import Thread
from github import Github
import jwt  # PyJWT library
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# --- Web Server (Detailed Health Check) ---
app = Flask('')

@app.route('/')
def home():
    return {
        "status": "online",
        "bot_name": "GT BOT",
        "message": "Server is running perfectly on Render"
    }, 200

def run_flask_server():
    try:
        port = int(os.environ.get("PORT", 10000))
        print(f"[SYSTEM] Starting Flask server on port {port}...")
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    except Exception as e:
        print(f"[ERROR] Flask Server failed: {e}")

# --- Configuration & Environment ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
GITHUB_TOKEN = os.environ.get("G_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")
REPO_NAME = "jjppjjpp0099-ux/OB53like-api"
RAILWAY_API = "https://xtytdtyj-jwt.up.railway.app/token"
VERCEL_LIKE_API = "https://ob-53like-api.vercel.app/like"
GROUP_ID = -1002316321534

# --- Helper Functions ---
def small_caps(text):
    normal = "abcdefghijklmnopqrstuvwxyz0123456789"
    fancy = "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ0123456789"
    trans = str.maketrans(normal, fancy)
    return str(text).lower().translate(trans)

async def check_admin(user):
    return str(user.id) == str(ADMIN_ID) or user.username == "ankitraj444"

# --- Advanced Logic: Expiry & GitHub ---
def is_token_expired(tokens):
    """Detailed check for JWT Expiry"""
    try:
        if not tokens or not isinstance(tokens, list):
            print("[AUTO] No tokens found in file. Triggering update...")
            return True
        
        first_token = tokens[0].get('token')
        if not first_token:
            return True

        # Decode JWT to check 'exp' claim
        decoded = jwt.decode(first_token, options={"verify_signature": False})
        expiry_timestamp = decoded.get('exp')
        
        if expiry_timestamp:
            time_remaining = expiry_timestamp - time.time()
            print(f"[AUTO] Token expires in {int(time_remaining)} seconds.")
            # If less than 10 minutes (600s) left, return True
            return time_remaining < 600
        return True
    except Exception as e:
        print(f"[ERROR] JWT Decode failed: {e}")
        return True

async def push_to_github(data_list, message):
    """Reliable GitHub File Update Logic"""
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        content = json.dumps(data_list, indent=4)
        
        try:
            file_ref = repo.get_contents("tokens.json")
            repo.update_file(file_ref.path, message, content, file_ref.sha)
            print(f"[GITHUB] Successfully updated tokens.json: {message}")
        except:
            repo.create_file("tokens.json", "Initial File Creation", content)
            print("[GITHUB] Created new tokens.json file.")
        return True
    except Exception as e:
        print(f"[ERROR] GitHub Push Error: {e}")
        return False

# --- Background Automation Engine ---
async def auto_refresh_engine(application):
    print("[SYSTEM] Auto Refresh Engine started...")
    await asyncio.sleep(20) # Initial wait for stability
    
    while True:
        try:
            print("[AUTO] Checking token status on GitHub...")
            g = Github(GITHUB_TOKEN)
            repo = g.get_repo(REPO_NAME)
            
            # Fetch Current Tokens
            try:
                remote_file = repo.get_contents("tokens.json")
                current_tokens = json.loads(remote_file.decoded_content.decode())
            except:
                current_tokens = []

            # Check if Update is Required
            if is_token_expired(current_tokens):
                print("[AUTO] Expiry detected! Fetching new tokens from Railway...")
                
                # Get Credentials
                cred_file = repo.get_contents("uidpass.json")
                credentials = json.loads(cred_file.decoded_content.decode())
                
                new_tokens_list = []
                async with aiohttp.ClientSession() as session:
                    for acc in credentials:
                        api_call = f"{RAILWAY_API}?uid={acc['uid']}&password={acc['password']}"
                        async with session.get(api_call) as response:
                            if response.status == 200:
                                data = await response.json()
                                if data.get("token"):
                                    new_tokens_list.append({"token": data.get("token")})
                
                if new_tokens_list:
                    success = await push_to_github(new_tokens_list, "Auto-Update: Tokens Refreshed")
                    if success:
                        await application.bot.send_message(chat_id=ADMIN_ID, text="🔄 **Auto update done**")
                else:
                    print("[AUTO] Failed to fetch any tokens from API.")
            else:
                print("[AUTO] Tokens are still valid. No action taken.")
        
        except Exception as e:
            print(f"[CRITICAL] Auto Engine Loop Error: {e}")
        
        await asyncio.sleep(60) # Wait for 1 minute before next check

# --- Command Handlers ---
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id == GROUP_ID or await check_admin(update.effective_user):
        user_name = small_caps(update.effective_user.first_name)
        welcome_text = (
            f"!! ʜᴇʏ {user_name} !!\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "ᴏᴡɴᴇʀ: @ankitraj444\n"
            "sᴛᴀᴛᴜs: ᴏɴʟɪɴᴇ ✅\n\n"
            "📜 ᴄᴏᴍᴍᴀɴᴅs:\n"
            "➥ /like [ʀᴇɢɪᴏɴ] [ᴜɪᴅ]\n"
            "➥ /update - ᴍᴀɴᴜᴀʟ ᴛᴏᴋᴇɴ ᴜᴘᴅᴀᴛᴇ\n"
            "➥ /check - ʀᴇᴘᴏ ᴄᴏɴɴᴇᴄᴛɪᴠɪᴛʏ\n"
            "━━━━━━━━━━━━━━━━━━━━"
        )
        await update.effective_chat.send_message(welcome_text)

async def like_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not (update.effective_chat.id == GROUP_ID or await check_admin(update.effective_user)):
        return

    if len(context.args) < 2:
        await update.effective_chat.send_message("❌ Usage: /like [region] [uid]")
        return

    region, uid = context.args[0].lower(), context.args[1]
    status_msg = await update.effective_chat.send_message("⌛ ᴘʀᴏᴄᴇssɪɴɢ ʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ...")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{VERCEL_LIKE_API}?uid={uid}&server_name={region}") as resp:
                result = await resp.json()

        if result.get("status") in [1, 2]:
            final_res = (
                "!! ʜᴇʏ ᴀɴᴋɪᴛ !!\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "💖 sᴜᴄᴄᴇssꜰᴜʟʟʏ ʟɪᴋᴇ sᴇɴᴛ\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "👤 ɴᴀᴍᴇ: " + str(result.get('PlayerNickname')) + "\n"
                "🆔 ᴜɪᴅ: " + str(uid) + "\n"
                "🌍 ʀᴇɢɪᴏɴ: " + region.upper() + "\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "👍 ʟɪᴋᴇs ʙᴇꜰᴏʀᴇ: " + str(result.get('LikesbeforeCommand')) + "\n"
                "❤️ ʟɪᴋᴇs ᴀꜰᴛᴇʀ: " + str(result.get('LikesafterCommand')) + "\n"
                "➕ ʟɪᴋᴇs ɢɪᴠᴇɴ: +20\n"
                "━━━━━━━━━━━━━━━━━━━━"
            )
            await status_msg.edit_text(final_res)
        else:
            await status_msg.edit_text(f"❌ Try next time. (Status: {result.get('status')})")
    except Exception as e:
        await status_msg.edit_text(f"😵 API Error: {e}")

async def update_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await check_admin(update.effective_user):
        context.user_data['waiting_for_file'] = True
        await update.effective_chat.send_message("📤 ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ `tokens.json` ꜰɪʟᴇ ᴛᴏ ᴜᴘᴅᴀᴛᴇ ᴍᴀɴᴜᴀʟʟʏ.")

async def file_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('waiting_for_file') and await check_admin(update.effective_user):
        document = update.message.document
        if document.file_name.endswith('.json'):
            progress = await update.effective_chat.send_message("⏳ ᴜᴘʟᴏᴀᴅɪɴɢ ᴛᴏ ɢɪᴛʜᴜʙ...")
            try:
                tg_file = await context.bot.get_file(document.file_id)
                content_bytes = await tg_file.download_as_bytearray()
                json_data = json.loads(content_bytes.decode('utf-8'))
                
                if await push_to_github(json_data, "Manual Update via Telegram"):
                    await progress.edit_text("✅ **Manual update done**")
                else:
                    await progress.edit_text("❌ GitHub Push Failed.")
            except Exception as e:
                await progress.edit_text(f"❌ Error: {e}")
            context.user_data['waiting_for_file'] = False

async def check_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await check_admin(update.effective_user):
        m = await update.effective_chat.send_message("🔍 ᴄʜᴇᴄᴋɪɴɢ sʏsᴛᴇᴍ ɪɴᴛᴇɢʀɪᴛʏ...")
        try:
            g = Github(GITHUB_TOKEN)
            repo = g.get_repo(REPO_NAME)
            await m.edit_text(f"✅ **Connected!**\nRepo: `{REPO_NAME}`\nBot Status: Active")
        except Exception as e:
            await m.edit_text(f"❌ Connection Failed: {e}")

# --- Main Application Runner ---
async def run_bot():
    print("[SYSTEM] Initializing Telegram Bot...")
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Registering Handlers
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("like", like_handler))
    application.add_handler(CommandHandler("update", update_command))
    application.add_handler(CommandHandler("check", check_handler))
    application.add_handler(MessageHandler(filters.Document.ALL, file_handler))
    
    # Starting Background Engine
    asyncio.create_task(auto_refresh_engine(application))
    
    # Core Bot Runner (Polished for Render)
    async with application:
        await application.initialize()
        await application.start()
        print("[SYSTEM] Bot Polling started.")
        await application.updater.start_polling(drop_pending_updates=True)
        
        # Keep Alive Loop
        stop_event = asyncio.Event()
        await stop_event.wait()

if __name__ == "__main__":
    # Start Web Server in separate thread
    flask_thread = Thread(target=run_flask_server, daemon=True)
    flask_thread.start()
    
    # Run the main async function
    try:
        asyncio.run(run_bot())
    except (KeyboardInterrupt, SystemExit):
        print("[SYSTEM] Bot stopped.")
