from telegram import CallbackQuery, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler
from telegram.error import BadRequest


class AbstractAction:
    def __init__(self, bot, action_key: str):
        self.bot = bot
        self.action_key = action_key

    def register(self):
        self.bot.register_action(self)

    async def handle(self, update: Update, ctx):
        print(f"Execution code for action '{self.action_key}' isn't implemented!")


class CallbackHandler(CallbackQueryHandler):
    def __init__(self, bot):
        super().__init__(self.handle_callback)
        self.bot = bot

    def register(self):
        self.bot.app.add_handler(self)

    async def handle_callback(self, update: Update, ctx):
        username = update.effective_user.username
        print(f'[Callback] Received callback action from @{username}.')

        query = update.callback_query
        await query.answer()

        data = query.data
        if data.startswith("#"):
            command_line = data[1:]
            args = command_line.split(' ')
            command = args.pop(0)

            action = None

            if command in self.bot.registered_actions.keys():
                action = self.bot.registered_actions[command]

            if action is None:
                print(f"[Callback] Invoked unknown action '{command}'!")
            else:
                try:
                    await action.handle(update, ctx)
                except BadRequest:
                    print(f"[Callback] Handle error: BadRequest")


class ActionShowCities(AbstractAction):
    def __init__(self, bot):
        super().__init__(bot, 'show_cities')
        self.keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton('г. Пермь', callback_data="#select_city perm"),
                InlineKeyboardButton('г. Москва', callback_data="#select_city moscow")
            ],
            [
                InlineKeyboardButton('с. Бырма', callback_data="#select_city birma"),
                InlineKeyboardButton('г. Кунгур', callback_data="#select_city kungur")
            ],
            [
                InlineKeyboardButton('г. Соликамск', callback_data="#select_city solikamsk"),
                InlineKeyboardButton('г. Париж', callback_data="#select_city paris")
            ]
        ])

    async def handle(self, update: Update, ctx):
        query = update.callback_query
        await self.show_cities(query.message.message_id, query.message.chat_id, query.inline_message_id)

    async def show_cities(self, message_id, chat_id, inline_message_id):
        if message_id is None and inline_message_id is None:
            await self.bot.get().send_message(
                chat_id,
                '🏙 Выберите город из списка:',
                reply_markup=self.keyboard
            )
        else:
            await self.bot.get().edit_message_text(
                '🏙 Выберите город из списка:',
                message_id=message_id,
                chat_id=chat_id,
                reply_markup=self.keyboard
            )
