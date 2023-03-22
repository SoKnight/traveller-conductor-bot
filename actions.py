from telegram import CallbackQuery, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CallbackQueryHandler
from telegram.error import BadRequest


class AbstractAction:
    def __init__(self, bot, action_key: str):
        self.bot = bot
        self.action_key = action_key

    async def handle(self, args: list, update: Update, ctx):
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
                await self.bot.get().send_message(query.message.chat_id, '😡 Не тыкайся...')
            else:
                try:
                    await action.handle(args, update, ctx)
                except BadRequest:
                    print(f"[Callback] Handle error: BadRequest")


class ActionShowCities(AbstractAction):
    def __init__(self, bot):
        super().__init__(bot, 'show_cities')

        buttons = [model.as_inline_button() for model in bot.city_models.values()]

        self.keyboard = InlineKeyboardMarkup([
            [buttons[0], buttons[1]],
            [buttons[2], buttons[3]],
            [buttons[4], buttons[5]]
        ])

    async def handle(self, args: list, update: Update, ctx):
        query = update.callback_query
        await self.show_cities(query.message.message_id, query.message.chat_id, query.inline_message_id)

    async def show_cities(self, message_id, chat_id, inline_message_id):
        if message_id is None and inline_message_id is None:
            await self.bot.get().send_message(
                chat_id,
                '🏘 Выберите город из списка:',
                reply_markup=self.keyboard
            )
        else:
            await self.bot.get().edit_message_text(
                '🏘 Выберите город из списка:',
                message_id=message_id,
                chat_id=chat_id,
                reply_markup=self.keyboard
            )


class ActionSelectCity(AbstractAction):
    def __init__(self, bot):
        super().__init__(bot, 'select_city')

    async def handle(self, args: list, update: Update, ctx):
        if len(args) < 1:
            print(f'[Callback] Failed: there are no city_id argument received!')
            return

        city_id = args[0]
        city = self.bot.get_city_model(city_id)

        holder = self.bot.get_user_holder(update.effective_user.id)
        holder.update_selected_city(city_id)

        await self.bot.get().send_message(
            update.callback_query.message.chat_id,
            f"""
*Выберите действие с городом*
            
{city.emoji} Город: `{city.name}`
🌍 Страна: `{city.country}`
""",
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=ActionSelectCity.construct_keyboard(city_id)
        )

    @staticmethod
    def construct_keyboard(city_id: str) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton('📚 Открыть справочник', callback_data=f'#show_city_info {city_id}')
            ],
            [
                InlineKeyboardButton('📷 Фото', callback_data=f'#show_photos {city_id}'),
                InlineKeyboardButton('🌤 Погода', callback_data=f'#show_weather {city_id}')
            ]
        ])
