from actions import *
from commands import *
from telegram import Update
from telegram.ext import Application, ApplicationBuilder, CallbackQueryHandler, CommandHandler, MessageHandler, ExtBot, filters
import yaml


class Preferences:
    def __init__(self, telegram_bot_token):
        self.telegram_bot_token = telegram_bot_token

    @staticmethod
    def load():
        file = open('preferences.yml', 'r', encoding='UTF-8')
        return yaml.load(file, yaml.Loader)


class Bot:
    def __init__(self):
        self.prefs = None
        self.token = None
        self.app = None

        self.registered_commands = dict()
        self.register_command(CommandStart(self))
        self.register_command(CommandBye(self))
        self.register_command(CommandHelp(self))

        self.registered_actions = dict()
        self.register_action(ActionShowCities(self))

    def app(self) -> Application:
        return self.app

    def get(self) -> ExtBot:
        return self.app.bot

    def load(self):
        print("""
-------------------------
 Traveller Conductor Bot
    written by @soknight
-------------------------
        """)

        print('Loading preferences...')
        self.prefs = Preferences.load()
        self.token = self.prefs.telegram_bot_token

        print('Initializing application...')
        self.app = ApplicationBuilder().token(self.token).build()

        print('Registering handlers...')
        self.register_handlers()

    def register_handlers(self):
        # command handlers
        for command in self.registered_commands.values():
            command.register()

        # callback handler
        CallbackHandler(self).register()

        # debugging
        self.app.add_handler(MessageHandler(filters.Sticker.ALL, Bot.show_received_sticker))

    def register_command(self, command: AbstractCommand):
        self.registered_commands[command.command] = command

    def register_action(self, action: AbstractAction):
        self.registered_actions[action.action_key] = action

    def start(self):
        print('Running LongPoll...')
        CallbackHandler(self).register()
        self.app.run_polling()

    @staticmethod
    async def show_received_sticker(update: Update, ctx):
        print(f"Received sticker message from @{update.effective_user.username}: {update.message.sticker}")


bot = Bot()
bot.load()
bot.start()
