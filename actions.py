from datetime import timedelta

from telegram import CallbackQuery, Update, InlineKeyboardMarkup, InputMediaPhoto
from telegram.constants import ParseMode
from telegram.ext import CallbackQueryHandler, ExtBot

from data import *
from weather import *


# Класс, абстрактно описывающий обработчик callback-действия с клавиатурой бота
# Обобщает метод обработки события и предоставляет доступ к объекту класса Bot
class AbstractAction:
    def __init__(self, bot, action_key: str):
        self.bot = bot
        self.action_key = action_key

    def get_city(self, _id: str) -> CityModel:
        data_loader: DataLoader = self.bot.data_loader
        return data_loader.get_city_model(_id)

    async def handle(self, args: list, update: Update, ctx):
        print(f"Execution code for action '{self.action_key}' isn't implemented!")


# Обработчик callback-событий, являющийся также диспетчером обработчиков действий
# При получении нового события находит подходящий обработчик действия и передаёт
# обработку события ему, иначе сообщает пользователю, что такого действия нет
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

        for line in data.split('\n'):
            if line.startswith('#'):
                command_line = line[1:]
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


# Класс, описывающий обработку действия по удалению сообщений
# Принимает внутри события идентификаторы сообщений и параллельно удаляет их
class ActionDeleteMessages(AbstractAction):
    def __init__(self, bot):
        super().__init__(bot, 'delete')

    async def handle(self, args: list, update: Update, ctx):
        if len(args) < 1:
            print(f'[Callback] Failed: there are no chat_id argument received!')
            return

        if len(args) < 2:
            print(f'[Callback] Failed: there are no message_id argument(s) received!')
            return

        bot: ExtBot = self.bot.get()
        chat_id = int(args.pop(0))
        coroutines = list()

        for message_id in args:
            message_id = int(message_id)
            coroutines.append(bot.delete_message(chat_id, message_id))

        for coroutine in coroutines:
            await coroutine


# Класс, описывающий обработку действия по отображению списка городов
# Ничего не требует от события, просто выводит статичную клавиатуру с городами
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


# Класс, описывающий обработку действия по выбору конкретного города
# Принимает внутри события ключ города и затем отображает клавиатуру
# с возможными действиями для этого города
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


# Класс, абстрактно описывающий то же действие, но применимое к городу
# Содержит готовый метод для отправки клавиатуры с действием возврата
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


# Класс, описывающий обработку действия по отображению информации о городе
# Аналогично выбору города получает его ключ, запрашивает информацию и выводит её
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


# Класс, описывающий обработку действия по отображению фото города
# Принимает внутри события ключ города, запрашивает идентификаторы
# загруженных на серверы Telegram фотографий и отправляет их в сообщении
class ActionShowPhotos(AbstractCityAction):
    def __init__(self, bot):
        super().__init__(bot, 'show_photos')

    async def handle(self, args: list, update: Update, ctx):
        if len(args) < 1:
            print(f'[Callback] Failed: there are no city_id argument received!')
            return

        city_id = args[0]
        city = self.get_city(city_id)

        query: CallbackQuery = update.callback_query

        if len(city.photos) == 0:
            await query.edit_message_text(
                f"""
*Фотографии города*

*Город:* {city.name} {city.emoji}

_К сожалению, фотографии пока отсутствуют :\\(_
_Мы обязательно добавим их позже\\._
                            """,
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=ActionShowPhotos.construct_keyboard(city_id)
            )
        else:
            media = list()

            for photo in city.photos:
                photo: CityPhoto
                media.append(InputMediaPhoto(photo.tg_id))

            await query.delete_message()

            sent_messages = await query.message.reply_media_group(media, protect_content=False)

            await query.message.reply_text(
                f"""
*Фотографии города*

*Город:* {city.name} {city.emoji}

Вот несколько фото выбранного города 🥺
Оригинальные источники доступны ниже\\.
                """,
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=ActionShowPhotos.construct_custom_keyboard(city_id, city, sent_messages)
            )

    @staticmethod
    def construct_custom_keyboard(city_id: str, city: CityModel, photos_messages: tuple):
        source_buttons = list()
        counter = 1

        for photo in city.photos:
            photo: CityPhoto
            source_buttons.append(InlineKeyboardButton(f"Источник #{counter}", url=photo.source))
            counter += 1

        chat_id = photos_messages[0].chat_id
        message_ids = ' '.join([str(message.message_id) for message in photos_messages])

        return InlineKeyboardMarkup([
            source_buttons,
            [
                InlineKeyboardButton(
                    '🎲 Вернуться к выбору действия',
                    callback_data=f'#delete {chat_id} {message_ids}\n#select_city {city_id}'
                )
            ]
        ])


# Класс, описывающий обработку действия по отображению актуальной погоды
# Принимает внутри события ключ города, запрашивает сохранённую в памяти
# информацию о погоде и выводит её в сообщении
class ActionShowWeather(AbstractCityAction):
    def __init__(self, bot):
        super().__init__(bot, 'show_weather')

    def get_weather_data(self, city_id: str) -> CityWeatherData:
        weather_service: WeatherService = self.bot.weather_service
        return weather_service.get_cached_weather_data(city_id)

    def get_condition(self, _id: int) -> WeatherCondition:
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

*Город:* {city.name} {city.emoji}

_К сожалению, информация в данный момент отстутствует :\\(_
_Это может быть вызвано техническими неполадками\\._
_Попробуйте повторить запрос позже\\._
                """,
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=ActionShowWeather.construct_keyboard(city_id)
            )
        else:
            local_datetime = datetime.utcnow() + timedelta(minutes=city.time_offset)
            gmt_offset = f'\\+{city.time_offset // 60}' if city.time_offset >= 0 else city.time_offset // 60

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

○ Местное время:  `{local_datetime.strftime('%d.%m.%y %H:%M:%S')}`  `GMT{gmt_offset}`
○ Температура:  `{round(weather_data.temp_c)}°C / {round(weather_data.temp_f)}°F`
○ Ощущается как:  `{round(weather_data.feelslike_c)}°C / {round(weather_data.feelslike_f)}°F`
○ Влажность:  `{weather_data.humidity}%`
○ Облачность:  `{weather_data.cloud}%`

Последнее обновление: *{update_time_ago} мин\\. назад*
                """,
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=ActionShowWeather.construct_keyboard(city_id)
            )
