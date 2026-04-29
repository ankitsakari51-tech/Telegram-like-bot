import aiohttp, os, asyncio, json, time
from flask import Flask
from threading import Thread
from github import Github
import jwt  # For checking token expiry
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# --- Web Server (Keep Alive) ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Online & Active"

def run():
    try:
        app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
    except Exception: pass

# --- Config & Environment Variables ---
B_TOKEN = os.environ.get("BOT_TOKEN")
G_TOKEN = os.environ.get("G_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")
REPO_NAME = "jjppjjpp0099-ux/OB53like-api"
JWT_API_URL = "https://xtytdtyj-jwt.up.railway.app/token"
LIKE_API = "https://ob-53like-api.vercel.app/like"
GRP = -1002316321534

# --- Utility Functions ---
def sc(t):
    n, s = "abcdefghijklmnopqrstuvwxyz0123456789", "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ0123456789"
    return str(t).lower().translate(str.maketrans(n, s))

async def is_o(u):
    return str(u.id) == str(ADMIN_ID) or u.username == "ankitraj444"

# --- Core Logic: Expiry Check ---
def check_expiry(token_list):
    """Checks if tokens are near expiration (within 10 minutes)"""
    try:
        if not token_list or 'token' not in token_list[0]:
            return True # No token means it's 'expired'
            
        t = token_list[0]['token']
        # Decode without verifying signature to just check 'exp'
        payload = jwt.decode(t, options={"verify_signature": False})
        exp_time = payload.get('exp')
        
        if exp_time:
            # Check if current time + 10 mins > expiry time
            if (time.time() + 600) > exp_time:
                return True
        return False
    except Exception as e:
        print(f"Expiry check error: {e}")
        return True

# --- GitHub File Manager ---
async def update_github_file(content_list, commit_msg):
    try:
        g = Github(G_TOKEN)
        repo = g.get_repo(REPO_NAME)
        json_string = json.dumps(content_list, indent=4)
        
        try:
            f = repo.get_contents("tokens.json")
            repo.update_file(f.path, commit_msg, json_string, f.sha)
        except:
            repo.create_file("tokens.json", "Initial Creation", json_string)
        return True
    except Exception as e:
        print(f"GitHub Update Failed: {e}")
        return False

# --- Auto Token Refresh Task ---
async def auto_refresh_loop(context: ContextTypes.DEFAULT_TYPE):
    while True:
        try:
            g = Github(G_TOKEN)
            repo = g.get_repo(REPO_NAME)
            
            # 1. Fetch current tokens.json to check expiry
            try:
                t_file = repo.get_contents("tokens.json")
                current_data = json.loads(t_file.decoded_content.decode())
            except:
                current_data = []

            if check_expiry(current_data):
                print("Auto-Update Triggered: Tokens expired or missing.")
                
                # 2. Get credentials from uidpass.json
                u_file = repo.get_contents("uidpass.json")
                u_data = json.loads(u_file.decoded_content.decode())
                
                fresh_tokens = []
                async with aiohttp.ClientSession() as session:
                    for acc in u_data:
                        api_url = f"{JWT_API_URL}?uid={acc['uid']}&password={acc['password']}"
                        async with session.get(api_url) as resp:
                            if resp.status == 200:
                                res_json = await resp.json()
                                if res_json.get("token"):
                                    fresh_tokens.append({"token": res_json.get("token")})
                
                if fresh_tokens:
                    success = await update_github_file(fresh_tokens, "Auto Update Done")
                    if success:
                        await context.bot.send_message(chat_id=ADMIN_ID, text="🔄 **Auto update done**")
                        print("Auto update successful.")
            else:
                print("Tokens are still valid. Cron ping skipped update.")
                
        except Exception as e:
            print(f"Background Loop Error: {e}")
            
        await asyncio.sleep(60) # Wait 1 minute

# --- Bot Command Handlers ---
async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if u.effective_chat.id == GRP or await is_o(u.effective_user):
        name = sc(u.effective_user.first_name)
        await u.effective_chat.send_message(f"Hey {name}!\nOwner: @ankitraj444\nCommands: /like, /update, /check")

async def like(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if not (u.effective_chat.id == GRP or await is_o(u.effective_user)): return
    if len(c.args) < 2:
        await u.effective_chat.send_message("❌ Use: /like region uid")
        return
    
    reg, uid = c.args[0].lower(), c.args[1]
    msg = await u.effective_chat.send_message("WAIT... ⏳")
    
    try:
        async with aiohttp.ClientSession() as ses:
            async with ses.get(f"{LIKE_API}?uid={uid}&server_name={reg}") as r:
                d = await r.json()
        
        if d.get("status") in [1, 2]:
            res = (f"╭━⟮ ✦ ᴘʟᴀʏᴇʀ ɪɴꜰᴏ ✦ ⟯\n│👤 ɴᴀᴍᴇ: {d.get('PlayerNickname')}\n"
                   f"│🆔 ᴜɪᴅ: {uid}\n│👍 ʟɪᴋᴇs: {d.get('LikesafterCommand')}\n╰━━━━━━━━━━━━━━━✪")
            await msg.edit_text(res)
        else:
            await msg.edit_text(f"Try later. Status: {d.get('status')}")
    except:
        await msg.edit_text("API Error 😵")

async def update_cmd(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if await is_o(u.effective_user):
        c.user_data['wait_file'] = True
        await u.effective_chat.send_message("📤 Send the `tokens.json` file to replace.")

async def handle_document(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if c.user_data.get('wait_file') and await is_o(u.effective_user):
        doc = u.message.document
        if doc.file_name.endswith('.json'):
            m = await u.effective_chat.send_message("⏳ Replacing file on GitHub...")
            try:
                f = await c.bot.get_file(doc.file_id)
                content = await f.download_as_bytearray()
                data = json.loads(content.decode())
                
                success = await update_github_file(data, "Manual Update via Bot")
                if success:
                    await m.edit_text("✅ **Manual update done**")
                else:
                    await m.edit_text("❌ GitHub Update Failed.")
            except Exception as e:
                await m.edit_text(f"Error: {e}")
            c.user_data['wait_file'] = False

async def check_repo(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if await is_o(u.effective_user):
        m = await u.effective_chat.send_message("🔍 Checking Repo...")
        try:
            r = Github(G_TOKEN).get_repo(REPO_NAME)
            await m.edit_text(f"✅ Connected: {REPO_NAME}\nEverything looks good!")
        except:
            await m.edit_text("❌ Repo Connection Error!")

# --- Main Initialization ---
if __name__ == "__main__":
    # Start Flask thread
    Thread(target=run, daemon=True).start()
    
    # Build Bot
    application = ApplicationBuilder().token(B_TOKEN).build()
    
    # Add Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("like", like))
    application.add_handler(CommandHandler("update", update_cmd))
    application.add_handler(CommandHandler("check", check_repo))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    # Start the Auto Refresh Task
    # Note: Running this inside the bot loop to use bot.send_message easily
    loop = asyncio.get_event_loop()
    asyncio.ensure_future(auto_refresh_loop(application))
    
    print("Bot is starting...")
    application.run_polling(drop_pending_updates=True)
