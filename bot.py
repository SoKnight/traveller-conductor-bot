from actions import *
from commands import *
from data import *
from telegram.ext import Application, ApplicationBuilder, ExtBot
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
        self.data_loader = None

        self.registered_commands = dict()
        self.registered_actions = dict()

    def app(self) -> Application:
        return self.app

    def get(self) -> ExtBot:
        return self.app.bot

    def load(self):
        print('Loading preferences...')
        self.prefs = Preferences.load()
        self.token = self.prefs.telegram_bot_token

        print('Loading data...')
        self.data_loader = DataLoader()
        self.data_loader.load()

        print('Initializing application...')
        self.app = ApplicationBuilder().token(self.token).build()

        print('Registering commands...')
        self.register_command(CommandStart(self))
        self.register_command(CommandBye(self))
        self.register_command(CommandHelp(self))

        print('Registering actions...')
        self.register_action(ActionShowCities(self))
        self.register_action(ActionSelectCity(self))
        self.register_action(ActionShowCityInfo(self))

        print('Registering handlers...')
        self.register_handlers()

    def register_handlers(self):
        # command handlers
        for command in self.registered_commands.values():
            command.register()

        # callback handler
        CallbackHandler(self).register()

    def register_command(self, command: AbstractCommand):
        self.registered_commands[command.command] = command

    def register_action(self, action: AbstractAction):
        self.registered_actions[action.action_key] = action

    def start(self):
        print('Running LongPoll...')
        CallbackHandler(self).register()
        self.app.run_polling()


print("""
-------------------------
 Traveller Conductor Bot
    written by @soknight
-------------------------
""")

bot = Bot()
bot.load()
bot.start()
