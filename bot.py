import yaml

from telegram.ext import Application, ApplicationBuilder, MessageHandler, CallbackContext
from telegram.ext.filters import *

from actions import *
from commands import *
from data import *
from weather import WeatherService


# Класс, описывающий структуру настроек в файле 'preferences.yml'
# Содержит атрибуты телеграм токена и API-ключа для weatherapi.com
class Preferences:
    def __init__(self, telegram_bot_token: str, weather_api_key: str):
        self.telegram_bot_token: str = telegram_bot_token
        self.weather_api_key: str = weather_api_key

    # При помощи данного метода реальные значения из файла
    # загружаются в атрибуты объекта посредством инструментария PyYAML
    @staticmethod
    def load():
        file = open('preferences.yml', 'r', encoding='UTF-8')
        return yaml.load(file, yaml.Loader)


# Главный класс всей программы, реализующий инициализацию всего
# функционала бота и различных дополнительных сервисов
class Bot:
    def __init__(self):
        self.prefs = None
        self.telegram_token = None
        self.weather_api_key = None
        self.app = None
        self.data_loader = None
        self.weather_service = None

        self.registered_commands = dict()
        self.registered_actions = dict()

    def app(self) -> Application:
        return self.app

    def get(self) -> ExtBot:
        return self.app.bot

    # Данный метод вызывается после создания объекта класса
    # и производит все действия, относящиеся к инициализации
    def load(self):
        print('Loading preferences...')
        self.prefs: Preferences = Preferences.load()
        self.telegram_token = self.prefs.telegram_bot_token
        self.weather_api_key = self.prefs.weather_api_key

        print('Loading data...')
        self.data_loader: DataLoader = DataLoader()
        self.data_loader.load()

        print('Initializing Weather Service...')
        self.weather_service: WeatherService = WeatherService(self)
        self.weather_service.start()

        print('Initializing application...')
        self.app = ApplicationBuilder().token(self.telegram_token).build()

        print('Registering commands...')
        self.register_command(CommandStart(self))
        self.register_command(CommandBye(self))
        self.register_command(CommandHelp(self))

        print('Registering actions...')
        self.register_action(ActionDeleteMessages(self))
        self.register_action(ActionShowCities(self))
        self.register_action(ActionSelectCity(self))
        self.register_action(ActionShowCityInfo(self))
        self.register_action(ActionShowPhotos(self))
        self.register_action(ActionShowWeather(self))

        print('Registering handlers...')
        self.register_handlers()

    # Вспомогательный метод для регистрации всех обработчиков,
    # ранее добавленных в списки регистрируемых
    def register_handlers(self):
        # command handlers
        for command in self.registered_commands.values():
            command.register()

        # callback handler
        CallbackHandler(self).register()

        # message handler
        app: Application = self.app
        app.add_handler(MessageHandler(filters=PHOTO | ATTACHMENT, callback=self.handle_user_photo_message))
        app.add_error_handler(callback=Bot.handle_error)

    def register_command(self, command: AbstractCommand):
        self.registered_commands[command.command] = command

    def register_action(self, action: AbstractAction):
        self.registered_actions[action.action_key] = action

    # Данный метод необходим для запуска основной петли,
    # блокирующей завершение программы и необходимой
    # для постоянного получения новых событий от Telegram API
    def start(self):
        print('Running LongPoll...')
        print('')

        CallbackHandler(self).register()
        self.app.run_polling()

    # Метод обработки события отправки фото пользователем,
    # необходимый для подготовки и отправки реакции от бота
    async def handle_user_photo_message(self, update: Update, ctx):
        has_photo: bool = False

        if update.message.document is not None:
            mime_type: str = update.message.document.mime_type
            if mime_type.startswith("image/"):
                has_photo = True

        if update.message.photo is not None and len(update.message.photo) != 0:
            has_photo = True

        if not has_photo:
            return

        data_loader: DataLoader = self.data_loader
        await update.message.reply_text(
            data_loader.get_random_photo_reaction(),
            reply_to_message_id=update.message.message_id
        )

    # Заглушка для обработки различных ошибок в python-telegram-bot
    @staticmethod
    async def handle_error(update, ctx: CallbackContext):
        error: Exception = ctx.error
        if error is None:
            return

        print("> An error was occurred during the mainloop processing:")
        print(f"  {error}")


# Вывод сплэша при запуске, инициализация бота и его запуск

print("""
-------------------------
 Traveller Conductor Bot
    written by @soknight
-------------------------
""")

bot = Bot()
bot.load()
bot.start()
