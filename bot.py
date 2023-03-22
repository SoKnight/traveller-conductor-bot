from actions import *
from commands import *
from telegram import InlineKeyboardButton
from telegram.ext import Application, ApplicationBuilder, ExtBot
import yaml


class Preferences:
    def __init__(self, telegram_bot_token):
        self.telegram_bot_token = telegram_bot_token

    @staticmethod
    def load():
        file = open('preferences.yml', 'r', encoding='UTF-8')
        return yaml.load(file, yaml.Loader)


class UserHolder:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.selected_city = None

    def update_selected_city(self, city_id: str):
        self.selected_city = city_id


class CityModel:
    def __init__(self, city_id: str, name: str, country: str, emoji: str):
        self.city_id = city_id
        self.name = name
        self.country = country
        self.emoji = emoji

    def as_inline_button(self):
        return InlineKeyboardButton(f'{self.emoji} {self.name}', callback_data=f'#select_city {self.city_id}')


class Bot:
    def __init__(self):
        self.prefs = None
        self.token = None
        self.app = None

        self.city_models = dict()
        self.city_models['perm'] = CityModel('perm', 'Пермь', 'Россия', '🐻')
        self.city_models['moscow'] = CityModel('moscow', 'Москва', 'Россия', '🇷🇺')
        self.city_models['kungur'] = CityModel('kungur', 'Кунгур', 'Россия', '🧊')
        self.city_models['birma'] = CityModel('birma', 'Бырма', 'Россия', '🏠')
        self.city_models['london'] = CityModel('london', 'Лондон', 'Великобритания', '🔪')
        self.city_models['paris'] = CityModel('paris', 'Париж', 'Франция', '🥖')

        self.user_holders = dict()

        self.registered_commands = dict()
        self.register_command(CommandStart(self))
        self.register_command(CommandBye(self))
        self.register_command(CommandHelp(self))

        self.registered_actions = dict()
        self.register_action(ActionShowCities(self))
        self.register_action(ActionSelectCity(self))

    def app(self) -> Application:
        return self.app

    def get(self) -> ExtBot:
        return self.app.bot

    def load(self):
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

    def register_command(self, command: AbstractCommand):
        self.registered_commands[command.command] = command

    def register_action(self, action: AbstractAction):
        self.registered_actions[action.action_key] = action

    def get_city_model(self, city_id: str) -> CityModel:
        return self.city_models[city_id]

    def get_user_holder(self, user_id: int) -> UserHolder:
        if user_id in self.user_holders.keys():
            return self.user_holders[user_id]
        else:
            holder = UserHolder(user_id)
            self.user_holders[user_id] = holder
            return holder

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
