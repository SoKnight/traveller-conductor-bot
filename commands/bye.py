from telegram import Update


async def execute(update: Update, ctx):
    await update.message.reply_text(
        f'👋 До новых встреч, {update.effective_user.first_name}!\n'
        '🥺 Буду ждать тебя здесь.'
    )
