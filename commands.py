from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler


# Класс, абстрактно описывающий исполнитель команды бота
# Обобщает метод выполнения команды и предоставляет доступ к объекту класса Bot
class AbstractCommand(CommandHandler):
    def __init__(self, bot, command: str):
        super().__init__(command, self.execute)
        self.bot = bot
        self.command = command

    def register(self):
        self.bot.app.add_handler(self)

    async def execute(self, update: Update, ctx):
        print(f"Execution code for command '{self.command}' isn't implemented!")


# Класс, описывающий исполнитель команды /start
# Выводит пользователю приветствие и статичную клавиатуру для быстрого действия
class CommandStart(AbstractCommand):
    def __init__(self, bot):
        super().__init__(bot, 'start')
        self.keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔎 Получить свежую информацию", callback_data="#show_cities")]
        ])

    async def execute(self, update: Update, ctx):
        await update.message.reply_text(
            f'🎉 Приветствую тебя, {update.effective_user.first_name}!',
            reply_markup=self.keyboard
        )


# Класс, описывающий исполнитель команды /bye
# Прощается с пользователем в сообщении
class CommandBye(AbstractCommand):
    def __init__(self, bot):
        super().__init__(bot, 'bye')

    async def execute(self, update: Update, ctx):
        await update.message.reply_text(
            f'👋 До новых встреч, {update.effective_user.first_name}!\n'
            '🥺 Буду ждать тебя здесь.'
        )


# Класс, описывающий исполнитель команды /help
# Выводит пользователю список городов, ссылаясь на реализацию этого
# функционала в аналогичном callback-действии
class CommandHelp(AbstractCommand):
    def __init__(self, bot):
        super().__init__(bot, 'help')

    async def execute(self, update: Update, ctx):
        await self.bot.registered_actions['show_cities'].show_cities(None, update.message.chat_id, None)
