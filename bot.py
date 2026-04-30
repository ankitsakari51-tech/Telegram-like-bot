import aiohttp, os, asyncio, json, time
from flask import Flask
from threading import Thread
from github import Github
import jwt  # Iske liye PyJWT zaruri hai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# --- Web Server (Keep Alive for Render) ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Online & Active"

def run():
    try:
        # Render default port 10000 use karta hai
        app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
    except Exception: pass

# --- Config ---
B_TOKEN = os.environ.get("BOT_TOKEN")
G_TOKEN = os.environ.get("G_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")
REPO_NAME = "jjppjjpp0099-ux/OB53like-api"
JWT_API_URL = "https://xtytdtyj-jwt.up.railway.app/token"
LIKE_API = "https://ob-53like-api.vercel.app/like"
GRP = -1002316321534

# --- Utility ---
def sc(t):
    n, s = "abcdefghijklmnopqrstuvwxyz0123456789", "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ0123456789"
    return str(t).lower().translate(str.maketrans(n, s))

async def is_o(u):
    return str(u.id) == str(ADMIN_ID) or u.username == "ankitraj444"

# --- Expiry Check Logic ---
def check_expiry(token_list):
    try:
        if not token_list or not isinstance(token_list, list) or 'token' not in token_list[0]:
            return True
        
        t = token_list[0]['token']
        # Decode without verification to get 'exp'
        payload = jwt.decode(t, options={"verify_signature": False})
        exp_time = payload.get('exp')
        
        # Agar 10 min se kam bacha hai toh refresh karo
        if exp_time and (time.time() + 600) > exp_time:
            return True
        return False
    except Exception as e:
        print(f"Expiry check error: {e}")
        return True

# --- GitHub Update Function ---
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
        print(f"GitHub Error: {e}")
        return False

# --- Auto Update Background Task ---
async def auto_refresh_loop(application):
    while True:
        try:
            g = Github(G_TOKEN)
            repo = g.get_repo(REPO_NAME)
            
            # Check current tokens
            try:
                t_file = repo.get_contents("tokens.json")
                current_data = json.loads(t_file.decoded_content.decode())
            except:
                current_data = []

            if check_expiry(current_data):
                print("Auto-update needed...")
                u_file = repo.get_contents("uidpass.json")
                u_data = json.loads(u_file.decoded_content.decode())
                
                fresh_tokens = []
                async with aiohttp.ClientSession() as session:
                    for acc in u_data:
                        api_url = f"{JWT_API_URL}?uid={acc['uid']}&password={acc['password']}"
                        async with session.get(api_url) as resp:
                            if resp.status == 200:
                                rj = await resp.json()
                                if rj.get("token"): fresh_tokens.append({"token": rj.get("token")})
                
                if fresh_tokens:
                    if await update_github_file(fresh_tokens, "Auto Update Done"):
                        await application.bot.send_message(chat_id=ADMIN_ID, text="🔄 **Auto update done**")
            else:
                print("Tokens are fresh. Skipping update.")
        except Exception as e:
            print(f"Loop Error: {e}")
            
        await asyncio.sleep(60) # Har 1 min check

# --- Bot Handlers ---
async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if u.effective_chat.id == GRP or await is_o(u.effective_user):
        await u.effective_chat.send_message(f"Hey {sc(u.effective_user.first_name)}!\nCommands: /like, /update, /check")

async def like(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if not (u.effective_chat.id == GRP or await is_o(u.effective_user)): return
    if len(c.args) < 2:
        await u.effective_chat.send_message("❌ /like region uid")
        return
    reg, uid = c.args[0].lower(), c.args[1]
    m = await u.effective_chat.send_message("⌛")
    try:
        async with aiohttp.ClientSession() as ses:
            async with ses.get(f"{LIKE_API}?uid={uid}&server_name={reg}") as r:
                d = await r.json()
        if d.get("status") in [1, 2]:
            await m.edit_text(f"✅ Sent to {d.get('PlayerNickname')}\nLikes: {d.get('LikesafterCommand')}")
        else:
            await m.edit_text(f"❌ Failed. Status: {d.get('status')}")
    except: await m.edit_text("Error 😵")

async def update_cmd(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if await is_o(u.effective_user):
        c.user_data['w'] = True
        await u.effective_chat.send_message("📤 Send `tokens.json` file now.")

async def handle_doc(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if c.user_data.get('w') and await is_o(u.effective_user):
        doc = u.message.document
        if doc.file_name.endswith('.json'):
            m = await u.effective_chat.send_message("⏳ Updating...")
            f = await c.bot.get_file(doc.file_id)
            b = await f.download_as_bytearray()
            if await update_github_file(json.loads(b.decode()), "Manual Update"):
                await m.edit_text("✅ **Manual update done**")
            else:
                await m.edit_text("❌ Failed.")
            c.user_data['w'] = False

async def check_repo(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if await is_o(u.effective_user):
        try:
            Github(G_TOKEN).get_repo(REPO_NAME)
            await u.effective_chat.send_message(f"✅ Connected to {REPO_NAME}")
        except: await u.effective_chat.send_message("❌ Connection Error")

# --- Fixed Main Runner for Render ---
async def main_runner():
    application = ApplicationBuilder().token(B_TOKEN).build()
    
    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("like", like))
    application.add_handler(CommandHandler("update", update_cmd))
    application.add_handler(CommandHandler("check", check_repo))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_doc))
    
    # Start Auto Task
    asyncio.create_task(auto_refresh_loop(application))
    
    # Start Bot Polling
    async with application:
        await application.initialize()
        await application.start_polling(drop_pending_updates=True)
        # Keep alive
        while True:
            await asyncio.sleep(3600)

if __name__ == "__main__":
    Thread(target=run, daemon=True).start()
    try:
        asyncio.run(main_runner())
    except (KeyboardInterrupt, SystemExit):
        pass
