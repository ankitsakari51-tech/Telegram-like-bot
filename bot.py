import aiohttp, os, asyncio, time
from flask import Flask
from threading import Thread
from github import Github
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# --- Web Server to keep bot alive & Receive Notifications ---
app = Flask('')

@app.route('/')
def home(): 
    return "Bot is Online"

# Naya Endpoint: Jab API token update karegi, wo is URL ko hit karegi
@app.route('/notify_update')
def notify_update():
    # Ye function group mein message bhej dega
    try:
        asyncio.run_coroutine_threadsafe(
            bot.bot.send_message(
                chat_id=GRP, 
                text="✅ **Token Auto Update Done**\nFresh tokens have been updated in GitHub."
            ),
            loop
        )
        return "OK", 200
    except Exception as e:
        return str(e), 500

def run_web_server():
    try:
        app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
    except Exception: 
        pass

# --- Background Pinger (Auto Update Trigger) ---
async def auto_pinger():
    """Ye loop har 5 minute mein Vercel API ko check karega"""
    while True:
        try:
            async with aiohttp.ClientSession() as ses:
                # Aapki Vercel API ka trigger route
                async with ses.get(f"{API_BASE}/trigger-update") as r:
                    print(f"Auto-check triggered: {r.status}")
        except Exception as e:
            print(f"Pinger Error: {e}")
        # 300 seconds = 5 minutes
        await asyncio.sleep(300)

# --- Config & IDs ---
B_TOKEN = os.environ.get("BOT_TOKEN")
G_TOKEN = os.environ.get("G_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")
REPO = "jjppjjpp0099-ux/OB53like-api" # Updated to your new repo
API_BASE = "https://ob-53like-api.vercel.app" # Aapka Vercel URL
API = f"{API_BASE}/like"
GRP = -1002316321534

def sc(t):
    if not t: return ""
    n = "abcdefghijklmnopqrstuvwxyz0123456789"
    s = "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ0123456789"
    trans = str.maketrans(n, s)
    return str(t).lower().translate(trans)

async def is_o(u):
    return str(u.id) == str(ADMIN_ID) or u.username == "ankitraj444"

# --- Bot Handlers ---
async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    chat, user = u.effective_chat, u.effective_user
    if chat.type == "private" and not await is_o(user):
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("DM OWNER", url="https://t.me/ankitraj444"),
            InlineKeyboardButton("GROUP", url="https://t.me/+pQxMtYP9OfxmZmE1")
        ]])
        await chat.send_message("⚠️ Private Bot. Use in official group.", reply_markup=kb)
    elif chat.id == GRP or await is_o(user):
        name = sc(user.first_name)
        await chat.send_message(f"Hey {name}!\nOwner: @ankitraj444\nCommands: /like, /update, /check")

async def like(u: Update, c: ContextTypes.DEFAULT_TYPE):
    chat, user = u.effective_chat, u.effective_user
    if (chat.type == "private" and not await is_o(user)) or (chat.id != GRP and not await is_o(user)):
        return
    if len(c.args) < 2:
        await chat.send_message("❌ Use: /like region uid")
        return
    
    reg, uid = c.args[0].lower(), c.args[1]
    msg = await chat.send_message("FETCHING... ⏳")
    
    try:
        async with aiohttp.ClientSession() as ses:
            async with ses.get(f"{API}?uid={uid}&server_name={reg}") as r:
                d = await r.json()
        
        api_status = d.get("status")
        if api_status not in [1, 2]:
            await msg.edit_text(f"Try next time 😵 (Status: {api_status})")
            return
            
        fname = sc(user.first_name)
        p_name = d.get('PlayerNickname', 'Unknown')
        l_before = d.get('LikesbeforeCommand', '0')
        l_added = d.get('LikesGivenByAPI', '0')
        l_after = d.get('LikesafterCommand', '0')

        res = (
            f"ㅤㅤㅤ!! ʜᴇʏ {fname} !!\n"
            f"✪━━━━━━━━━━━━━━━✪\n"
            f"╭💝\n"
            f"│ꜱᴜᴄᴄᴇssꜰᴜʟʟʏ ʟɪᴋᴇ ꜱᴇɴᴛ\n"
            f"╰━━━━━━━━━━━━━━━✪\n\n"
            f"╭━⟮ ✦ ᴘʟᴀʏᴇʀ ɪɴꜰᴏ ✦ ⟯\n"
            f"│👤 ɴᴀᴍᴇ: {p_name}\n"
            f"│🆔 ᴜɪᴅ: {uid}\n"
            f"│🌍 ʀᴇɢɪᴏɴ: {reg.upper()}\n"
            f"╰━━━━━━━━━━━━━━━✪\n\n"
            f"╭━⟮ ✦ ʟɪᴋᴇ ᴅᴇᴛᴀɪʟꜱ ✦ ⟯\n"
            f"│👍 ʟɪᴋᴇs ʙᴇꜰᴏʀᴇ:  {l_before}\n"
            f"│❤️ ʟɪᴋᴇs ᴀꜰᴛᴇʀ:    {l_after}\n"
            f"│➕ ʟɪᴋᴇs ɢɪᴠᴇɴ:   +{l_added}\n"
            f"╰━━━━━━━━━━━━━━━✪"
        )
        await msg.edit_text(res)
    except Exception as e:
        print(f"Error: {e}")
        await msg.edit_text("Error 😵")

async def up(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if await is_o(u.effective_user):
        c.user_data['u'] = True
        await u.effective_chat.send_message("📤 Send tokens.json file now to update GitHub.")

async def check_repo(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if await is_o(u.effective_user):
        m = await u.effective_chat.send_message("🔍 Checking GitHub Connection...")
        try:
            r = Github(G_TOKEN).get_repo(REPO)
            files = [f.path for f in r.get_contents("")]
            status = "✅ GitHub Connected!\n\n"
            # Updated to only check tokens.json as per your request
            p = "tokens.json"
            status += f"● {p}: {'Found' if p in files else 'Not Found'}\n"
            await m.edit_text(status)
        except Exception as e:
            await m.edit_text(f"❌ Connection Error: {e}")

async def doc(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if c.user_data.get('u') and await is_o(u.effective_user):
        d = u.message.document
        if d and d.file_name == 'tokens.json':
            m = await u.effective_chat.send_message("⏳ Updating GitHub File...")
            try:
                f = await c.bot.get_file(d.file_id)
                b = await f.download_as_bytearray()
                r = Github(G_TOKEN).get_repo(REPO)
                
                rf = r.get_contents("tokens.json")
                r.update_file(rf.path, "Bot Manual Update", bytes(b), rf.sha)
                await m.edit_text("✅ GitHub tokens.json Updated Successfully!")
            except Exception as e:
                await m.edit_text(f"Update Failed: {e}")
            c.user_data['u'] = False

# --- Main Execution ---
if __name__ == "__main__":
    # Get the event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Start Web Server in Thread
    Thread(target=run_web_server, daemon=True).start()
    
    # Start the Auto-Pinger in the background
    def start_pinger():
        asyncio.run(auto_pinger())
    Thread(target=start_pinger, daemon=True).start()

    # Build Bot
    bot = ApplicationBuilder().token(B_TOKEN).build()
    
    # Add Handlers
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("like", like))
    bot.add_handler(CommandHandler("update", up))
    bot.add_handler(CommandHandler("check", check_repo))
    bot.add_handler(MessageHandler(filters.Document.ALL, doc))
    
    # Run Bot
    bot.run_polling(drop_pending_updates=True)
