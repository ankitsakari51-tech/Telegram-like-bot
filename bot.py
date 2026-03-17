import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from github import Github

# --- 1. APNI SETTINGS YAHAN BHAREIN ---
TOKEN = os.environ.get('TELEGRAM_TOKEN') # Aapka purana bot token
GITHUB_TOKEN = os.environ.get('G_TOKEN') # Jo abhi aapne banaya
REPO_NAME = 'ankitsakari51-tech/Telegram-like-bot'
ADMIN_ID = int(os.environ.get('ADMIN_ID')) # Apni Telegram User ID yahan likhein (Numbers mein)

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- PURANA CODE WALA START COMMAND ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is Running! Purane features bhi kaam kar rahe hain.")

# --- NAYA GITHUB UPDATE FEATURE ---
async def update_files_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Aap admin nahi hain!")
        return
    
    context.user_data['waiting_for_json'] = True
    await update.message.reply_text("📤 Ok! Ab `token_ind.json` ya `token_ind_visit.json` file bhejiye.")

async def handle_docs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if we are waiting for a file
    if not context.user_data.get('waiting_for_json'):
        return

    doc = update.message.document
    file_name = doc.file_name

    # Check correct file names
    if file_name in ["token_ind.json", "token_ind_visit.json"]:
        status_msg = await update.message.reply_text(f"⏳ {file_name} ko GitHub par update kar raha hoon...")
        
        try:
            # Download from Telegram
            tg_file = await doc.get_file()
            content = await tg_file.download_as_bytearray()

            # Connect to GitHub
            g = Github(GITHUB_TOKEN)
            repo = g.get_repo(REPO_NAME)
            
            # Get old file and update it
            contents = repo.get_contents(file_name)
            repo.update_file(contents.path, f"Update {file_name} via Bot", bytes(content), contents.sha)
            
            await status_msg.edit_text(f"✅ {file_name} Successfully Update ho gaya!")
            # Kaam hone ke baad state reset kar dein
            context.user_data['waiting_for_json'] = False
            
        except Exception as e:
            await status_msg.edit_text(f"❌ Error: {str(e)}")
    else:
        await update.message.reply_text("⚠️ Ye galat file hai. Please sirf JSON files hi bhejiye.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    # Handlers (Purane aur Naye dono)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("update_files", update_files_command))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_docs))

    print("Bot is starting...")
    app.run_polling()
    app_tele.add_handler(CommandHandler("like", like_command))
    
    print("Bot is running with keep-alive...")
    app_tele.run_polling()

if __name__ == "__main__":
    main()
