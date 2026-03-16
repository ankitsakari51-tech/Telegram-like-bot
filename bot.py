import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = "8616498366:AAFArnjNJ24ZnQTcNRNBCCoeoUP3aDRu9WQ"
OWNER_NAME = "@ankitraj444"
API_URL = "https://like-api-2-zy52.vercel.app/like"

ALLOWED_GROUP = -1002316321534   # 👉 यहाँ अपना group id डालो


def small_caps(text: str) -> str:
    normal = "abcdefghijklmnopqrstuvwxyz"
    small = "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ"
    return text.lower().translate(str.maketrans(normal, small))


async def send_styled(update: Update, text: str):
    await update.message.reply_text(small_caps(text))


async def private_message(update: Update):

    buttons = [
        [
            InlineKeyboardButton("DM OWNER", url="https://t.me/ankitraj444"),
            InlineKeyboardButton("LIKE GROUP", url="https://t.me/+pQxMtYP9OfxmZmE1")
        ]
    ]

    reply_markup = InlineKeyboardMarkup(buttons)

    await update.message.reply_text(
        "⚠️ This bot is private. Use it only in the official group.",
        reply_markup=reply_markup
    )


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_chat.id != ALLOWED_GROUP:
        await private_message(update)
        return

    user_name = update.effective_user.first_name
    msg = (
        f"Hey! {user_name} nice to meet you 😊\n\n"
        f"👑 owner: {OWNER_NAME}\n\n"
        "📌 available command:\n"
        "/like region uid\n\n"
        "example:\n"
        "/like ind 123456789\n"
        "more command type /help"
    )
    await send_styled(update, msg)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_chat.id != ALLOWED_GROUP:
        await private_message(update)
        return

    msg = (
        "📖 HELP MENU\n\n"
        "✅ /start - Bot start karne ke liye\n"
        "✅ /like region uid - Free Fire like bhejne ke liye\n\n"
        "Example:\n"
        "/like ind 123456789\n\n"
        f"👑 Owner: {OWNER_NAME}"
    )
    await send_styled(update, msg)


async def like_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_chat.id != ALLOWED_GROUP:
        await private_message(update)
        return

    if len(context.args) < 2:
        await send_styled(update, "use: /like region uid\nexample: /like ind 123456789")
        return

    region = context.args[0].lower()
    uid = context.args[1]

    await send_styled(update, "fetching player data... ⏳")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_URL}?uid={uid}&server_name={region}") as response:
                data = await response.json()

        if data.get("status") != 1:
            await send_styled(update, "Try next day api error 😵")
            return

        name = data.get("PlayerNickname", "Unknown")
        before = data.get("LikesbeforeCommand", 0)
        after = data.get("LikesafterCommand", 0)
        given = data.get("LikesGivenByAPI", 0)

        msg = f"""
🔥 PLAYER PROFILE

👤 Name : {name}
🆔 UID : {uid}
🌍 Region : {region}

👍 Before Likes : {before}
❤️ Likes Given : +{given}
🔥 After Likes : {after}
"""
        await send_styled(update, msg)

    except Exception as e:
        await send_styled(update, "api error aa gaya 😵")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("like", like_command))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
