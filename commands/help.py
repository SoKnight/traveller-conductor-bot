from telegram import Update


async def execute(update: Update, ctx):
    await update.message.reply_text('🥱 Данный функционал недоступен...')
    await update.message.reply_sticker('CAACAgIAAxkBAAMoZBTO1tI974ZzjdQc4o3WWSrbUVUAAp0UAAIXYBFIqfeitFT4smIvBA')
