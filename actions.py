import math

from data import *
from weather import *
from datetime import datetime, timedelta
from telegram import CallbackQuery, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CallbackQueryHandler
from telegram.error import BadRequest


class AbstractAction:
    def __init__(self, bot, action_key: str):
        self.bot = bot
        self.action_key = action_key

    def get_city(self, _id: str) -> CityModel:
        data_loader: DataLoader = self.bot.data_loader
        return data_loader.get_city_model(_id)

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
                await action.handle(args, update, ctx)


class ActionShowCities(AbstractAction):
    def __init__(self, bot):
        super().__init__(bot, 'show_cities')

        buttons = [model.as_inline_button() for model in bot.data_loader.city_models.values()]

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

        city = self.get_city(args[0])
        query: CallbackQuery = update.callback_query

        await query.edit_message_text(
            f"""
*Выберите действие с городом*
            
{city.emoji} Город: `{city.name}`
🌍 Страна: `{city.country}`
            """,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=ActionSelectCity.construct_keyboard(args[0])
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
            ],
            [
                InlineKeyboardButton('🏘 Выбрать другой город', callback_data=f'#show_cities')
            ]
        ])


class AbstractCityAction(AbstractAction):
    def __init__(self, bot, action_key: str):
        super().__init__(bot, action_key)

    @staticmethod
    def construct_keyboard(city_id: str) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton('🎲 Вернуться к выбору действия', callback_data=f'#select_city {city_id}')
            ]
        ])


class ActionShowCityInfo(AbstractCityAction):
    def __init__(self, bot):
        super().__init__(bot, 'show_city_info')

    async def handle(self, args: list, update: Update, ctx):
        if len(args) < 1:
            print(f'[Callback] Failed: there are no city_id argument received!')
            return

        city_id = args[0]
        city = self.get_city(city_id)

        query: CallbackQuery = update.callback_query

        await query.edit_message_text(
            f"""
*Справка о городе {city.name} {city.emoji}*

○ Страна: `{city.country}`
○ Широта: `{city.latitude}`
○ Долгота: `{city.longitude}`
○ Площадь: `{city.area} км²`
○ Население: `{city.population}`
            """,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=ActionShowCityInfo.construct_keyboard(city_id)
        )


class ActionShowWeather(AbstractCityAction):
    def __init__(self, bot):
        super().__init__(bot, 'show_weather')

    def get_weather_data(self, city_id: str) -> CityWeatherData | None:
        weather_service: WeatherService = self.bot.weather_service
        return weather_service.get_cached_weather_data(city_id)

    def get_condition(self, _id: int) -> WeatherCondition | None:
        data_loader: DataLoader = self.bot.data_loader
        return data_loader.get_weather_condition(_id)

    async def handle(self, args: list, update: Update, ctx):
        if len(args) < 1:
            print(f'[Callback] Failed: there are no city_id argument received!')
            return

        city_id = args[0]
        city = self.get_city(city_id)

        query: CallbackQuery = update.callback_query

        weather_data = self.get_weather_data(city_id)
        if weather_data is None:
            await query.edit_message_text(
                f"""
*Информация о текущей погоде*

○ Город: `{city.name}` {city.emoji}

_К сожалению, информация в данный момент отстутствует :(_
_Это может быть вызвано различными техническими неполадками._
_Попробуйте повторить запрос позже._
                """,
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=ActionShowWeather.construct_keyboard(city_id)
            )
        else:
            condition: WeatherCondition = self.get_condition(weather_data.condition_code)
            condition_text: str = condition.get_text(weather_data.is_day)
            condition_emoji: str = condition.get_emoji(weather_data.is_day)

            time_delta: timedelta = datetime.now() - weather_data.date_time
            update_time_ago: int = round(time_delta.total_seconds() / 60.0)

            if update_time_ago == 0:
                update_time_ago = 1

            await query.edit_message_text(
                f"""
*Информация о текущей погоде*

*Город:* {city.name} {city.emoji}
_{condition_text}_ {condition_emoji}

○ Температура: `{round(weather_data.temp_c)}°C` */* `{round(weather_data.temp_f)}°F`
○ Ощущается как: `{round(weather_data.feelslike_c)}°C` */* `{round(weather_data.feelslike_f)}°F`
○ Влажность: `{weather_data.humidity}%`
○ Облачность: `{weather_data.cloud}%`

Последнее обновление: *{update_time_ago} мин\\. назад*\\.
                """,
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=ActionShowWeather.construct_keyboard(city_id)
            )
