from telegram import Update


async def execute(update: Update, ctx):
    await update.message.reply_text(
        f'🎉 Приветствую тебя, {update.effective_user.first_name}!\n'
        '🔎 Используй команду /help, чтобы получить свежую информацию.'
    )
    await update.message.reply_sticker('CAACAgIAAxkBAAMzZBTR4Q47ip1QGEwKxbOBArQM6oQAAo4VAALlo-lJPKEkTiVH1L0vBA')
