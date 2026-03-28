import aiohttp, os, asyncio
from flask import Flask
from threading import Thread
from github import Github
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# --- Web Server to keep bot alive ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Online"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

# --- Config & IDs ---
B_TOKEN = os.environ.get("BOT_TOKEN")
G_TOKEN = os.environ.get("G_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")
REPO = "jjppjjpp0099-ux/Like-api-2"
API = "https://like-api-2-zy52.vercel.app/like"
GRP = -1002316321534

def sc(t):
    n = "abcdefghijklmnopqrstuvwxyz0123456789"
    s = "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ0123456789"
    return t.lower().translate(str.maketrans(n, s))

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
        await chat.send_message(sc(f"Hey {user.first_name}!\nOwner: @ankitraj444\nCommands: /like, /help"))

async def like(u: Update, c: ContextTypes.DEFAULT_TYPE):
    chat, user = u.effective_chat, u.effective_user
    if (chat.type == "private" and not await is_o(user)) or (chat.id != GRP and not await is_o(user)):
        return
    if len(c.args) < 2:
        await chat.send_message(sc("use: /like region uid"))
        return
    
    reg, uid = c.args[0].lower(), c.args[1]
    msg = await chat.send_message(sc("FETCHING... ⏳"))
    
    try:
        async with aiohttp.ClientSession() as ses:
            async with ses.get(f"{API}?uid={uid}&server_name={reg}") as r:
                d = await r.json()
        
        if d.get("status") != 1:
            await msg.edit_text(sc("try next time 😵"))
            return
            
        # Naya Stylish Format according to screenshot
        res = (
            f"     {sc('HEY')} {sc(user.first_name)} !!\n"
            f"✪━━━━━━━━━━━━━━━✪\n"
            f"╭💝\n"
            f"│{sc('ꜱᴜᴄᴄᴇssꜰᴜʟʟʏ ʟɪᴋᴇ ꜱᴇɴᴛ')}\n"
            f"╰━━━━━━━━━━━━━━━✪\n\n"
            f"╭━⟮ ✦ {sc('ᴘʟᴀʏᴇʀ ɪɴꜰᴏ')} ✦ ⟯\n"
            f"│👤 {sc('ɴᴀᴍᴇ')}: {d.get('PlayerNickname')}\n"
            f"│🆔 {sc('ᴜɪᴅ')}: {uid}\n"
            f"│🌍 {sc('ʀᴇɢɪᴏɴ')}: {reg.upper()}\n"
            f"╰━━━━━━━━━━━━━━━✪\n\n"
            f"╭━⟮ ✦ {sc('ʟɪᴋᴇ ᴅᴇᴛᴀɪʟꜱ')} ✦ ⟯\n"
            f"│👍 {sc('ʟɪᴋᴇs ʙᴇꜰᴏʀᴇ')}: {d.get('LikesbeforeCommand')}\n"
            f"│❤️ {sc('ʟɪᴋᴇs ᴀꜰᴛᴇʀ')}:    {d.get('LikesafterCommand')}\n"
            f"│➕ {sc('ʟɪᴋᴇs ɢɪᴠᴇɴ')}:   +{d.get('LikesGivenByAPI')}\n"
            f"╰━━━━━━━━━━━━━━━✪"
        )
        await msg.edit_text(res)
    except Exception:
        await msg.edit_text(sc("Error 😵"))

async def up(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if await is_o(u.effective_user):
        c.user_data['u'] = True
        await u.effective_chat.send_message("📤 Send .json")

async def doc(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if c.user_data.get('u') and await is_o(u.effective_user):
        d = u.message.document
        if d and d.file_name.endswith('.json'):
            m = await u.effective_chat.send_message("⏳ Updating...")
            f = await c.bot.get_file(d.file_id)
            b = await f.download_as_bytearray()
            r = Github(G_TOKEN).get_repo(REPO)
            for p in ["token_ind.json", "token_ind_visit.json"]:
                rf = r.get_contents(p)
                r.update_file(rf.path, "Update", bytes(b), rf.sha)
            await m.edit_text("✅ Done!")
            c.user_data['u'] = False

if __name__ == "__main__":
    Thread(target=run, daemon=True).start()
    bot = ApplicationBuilder().token(B_TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("like", like))
    bot.add_handler(CommandHandler("update", up))
    bot.add_handler(MessageHandler(filters.Document.ALL, doc))
    bot.run_polling(drop_pending_updates=True)
