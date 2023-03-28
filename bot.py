from actions import *
from commands import *
from data import *
from weather import WeatherFetchThread
from telegram.ext import Application, ApplicationBuilder, ExtBot
import yaml


class Preferences:
    def __init__(self, telegram_bot_token: str, weather_api_key: str):
        self.telegram_bot_token: str = telegram_bot_token
        self.weather_api_key: str = weather_api_key

    @staticmethod
    def load():
        file = open('preferences.yml', 'r', encoding='UTF-8')
        return yaml.load(file, yaml.Loader)


class Bot:
    def __init__(self):
        self.prefs = None
        self.telegram_token = None
        self.weather_api_key = None
        self.app = None
        self.data_loader = None
        self.weather_thread = None

        self.registered_commands = dict()
        self.registered_actions = dict()

    def app(self) -> Application:
        return self.app

    def get(self) -> ExtBot:
        return self.app.bot

    def load(self):
        print('Loading preferences...')
        self.prefs: Preferences = Preferences.load()
        self.telegram_token = self.prefs.telegram_bot_token
        self.weather_api_key = self.prefs.weather_api_key

        print('Loading data...')
        self.data_loader: DataLoader = DataLoader()
        self.data_loader.load()

        print('Initializing application...')
        self.app = ApplicationBuilder().token(self.telegram_token).build()

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

        print('Running Weather Service thread...')
        self.weather_thread: WeatherFetchThread = WeatherFetchThread(self)
        self.weather_thread.start()

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
