from commands import start
from commands import bye
from commands import help
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ExtBot, filters
import yaml


class Preferences:
    def __init__(self, telegram_bot_token):
        self.telegram_bot_token = telegram_bot_token

    @staticmethod
    def load():
        file = open('preferences.yml', 'r', encoding='UTF-8')
        return yaml.load(file, yaml.Loader)


def get_bot() -> ExtBot:
    return app.bot


async def debug_stickers(update: Update, ctx):
    print(f"Received sticker message from @{update.effective_user.username}: {update.message.sticker}")


print("""
-------------------------
 Traveller Conductor Bot
    written by @soknight
-------------------------
""")

print('Loading preferences...')
prefs = Preferences.load()
token = prefs.telegram_bot_token

print('Initializing application...')
app = ApplicationBuilder().token(token).build()
app.add_handler(CommandHandler("start", start.execute))
app.add_handler(CommandHandler("bye", bye.execute))
app.add_handler(CommandHandler("help", help.execute))
# app.add_handler(MessageHandler(filters.Sticker.ALL, debug_stickers))

print('Running LongPoll...')
print()
app.run_polling()
