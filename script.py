#
# API_ID = 38827239  # my.telegram.org dan olgan api_id
# API_HASH = "2ead2681c9fa7bf3bc9f61cede0e069a"  # my.telegram.org dan olgan api_hash
# BOT_TOKEN = "7260819449:AAGsz-PZKMnSsgqMs2hyc-qziCj0wXK5h7M"  # @BotFather dan olgan bot tokeni
# ADMIN_ID = 5992695620  # Sizning shaxsiy Telegram ID raqamingiz

import asyncio
from datetime import datetime
from pyrogram import Client
from telegram import Bot
from telegram.ext import Application, CommandHandler, ContextTypes

# ==================== SOZLAMALAR ====================
API_ID = 38827239  # my.telegram.org dan olgan api_id
API_HASH = "2ead2681c9fa7bf3bc9f61cede0e069a"  # my.telegram.org dan olgan api_hash
BOT_TOKEN = "7260819449:AAGsz-PZKMnSsgqMs2hyc-qziCj0wXK5h7M"  # @BotFather dan olgan bot tokeni
ADMIN_ID = 5992695620  # Sizning shaxsiy Telegram ID raqamingiz
# ====================================================

app = Client("my_tracker_session", api_id=API_ID, api_hash=API_HASH)

tracked_users = {}
bot_application = None


# Barqaror fon tekshiruvi (Timeout xatosi chiqmasligi uchun 5 sekund qilib belgilandi)
async def status_checker():
    await asyncio.sleep(3)
    print("🟢 Kuzatuv tizimi barqaror rejimda ishga tushdi!")

    while True:
        if tracked_users and bot_application:
            for target_key in list(tracked_users.keys()):
                try:
                    user = await app.get_users(target_key)
                    status = user.status
                    data = tracked_users[target_key]

                    # Onlayn bo'lsa
                    if str(status) == "UserStatus.ONLINE" and not data["is_online"]:
                        data["is_online"] = True
                        data["start_time"] = datetime.now()

                        time_str = data["start_time"].strftime('%H:%M:%S')
                        msg = f"🟢 **{target_key}** onlayn bo'ldi!\n⏰ Vaqt: `{time_str}`"
                        await bot_application.bot.send_message(chat_id=ADMIN_ID, text=msg, parse_mode="Markdown")

                    # Oflayn bo'lsa
                    elif str(status) != "UserStatus.ONLINE" and data["is_online"]:
                        data["is_online"] = False
                        end_time = datetime.now()
                        duration = end_time - data["start_time"]

                        minutes = int(duration.total_seconds() // 60)
                        seconds = int(duration.total_seconds() % 60)

                        start_str = data["start_time"].strftime('%H:%M:%S')
                        end_str = end_time.strftime('%H:%M:%S')

                        msg = (
                            f"🔴 **{target_key}** oflayn bo'ldi!\n"
                            f"🟢 Kirgan: `{start_str}`\n"
                            f"🔴 Chiqqan: `{end_str}`\n"
                            f"⏱ Onlayn vaqti: `{minutes} daqiqa {seconds} soniya`"
                        )
                        await bot_application.bot.send_message(chat_id=ADMIN_ID, text=msg, parse_mode="Markdown")

                except Exception as e:
                    pass

        # Timeout xatosi chiqmasligi uchun optimal va xavfsiz interval: 5 sekund
        await asyncio.sleep(5)


async def start_cmd(update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text(
        "👋 Salom! Men foydalanuvchilarning statusini kuzatuvchi barqaror botman.\n\n"
        "Buyruqlar:\n"
        "🔸 `/track ID_yoki_username` - Kuzatish\n"
        "🔸 `/stop ID_yoki_username` - To'xtatish\n"
        "🔸 `/list` - Ro'yxat",
        parse_mode="Markdown"
    )


async def track_cmd(update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("❌ ID yoki username kiriting.\nMasalan: `/track 8204064509`",
                                        parse_mode="Markdown")
        return

    raw_target = context.args[0]
    target = int(raw_target) if raw_target.isdigit() else raw_target.replace("@", "")

    tracked_users[target] = {"is_online": False, "start_time": None}
    await update.message.reply_text(f"✅ `{target}` kuzatuv ro'yxatiga qo'shildi!", parse_mode="Markdown")


async def stop_cmd(update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("❌ O'chirish uchun ID yoki username kiriting.", parse_mode="Markdown")
        return

    raw_target = context.args[0]
    target = int(raw_target) if raw_target.isdigit() else raw_target.replace("@", "")

    if target in tracked_users:
        del tracked_users[target]
        await update.message.reply_text(f"🛑 `{target}` kuzatuvdan olib tashlandi.", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"⚠️ `{target}` ro'yxatdan topilmadi.", parse_mode="Markdown")


async def list_cmd(update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not tracked_users:
        await update.message.reply_text("📋 Hozircha hech kim kuzatilmayapti.")
        return

    text = "📋 **Kuzatuvdagi foydalanuvchilar:**\n\n"
    for user in tracked_users:
        text += f"• `{user}`\n"
    await update.message.reply_text(text, parse_mode="Markdown")


async def main():
    global bot_application

    bot_application = Application.builder().token(BOT_TOKEN).build()

    bot_application.add_handler(CommandHandler("start", start_cmd))
    bot_application.add_handler(CommandHandler("track", track_cmd))
    bot_application.add_handler(CommandHandler("stop", stop_cmd))
    bot_application.add_handler(CommandHandler("list", list_cmd))

    async with app:
        await bot_application.initialize()
        await bot_application.start()
        await bot_application.updater.start_polling()

        asyncio.create_task(status_checker())

        print("🟢 Bot va Kuzatuv tizimi muvaffaqiyatli ishga tushdi!")

        stop_event = asyncio.Event()
        await stop_event.wait()


if __name__ == "__main__":
    asyncio.run(main())