from telegram import InlineKeyboardButton
import json


class CityModel:
    def __init__(self, city_id: str, data: dict):
        self.city_id = city_id
        self.name = data['name']
        self.country = data['country']
        self.emoji = data['emoji']
        self.latitude = data['latitude']
        self.longitude = data['longitude']
        self.raw_lat = data['lat']
        self.raw_lon = data['lon']
        self.area = data['area']
        self.population = data['population']

    def as_inline_button(self):
        return InlineKeyboardButton(f'{self.emoji} {self.name}', callback_data=f'#select_city {self.city_id}')


class WeatherCondition:
    def __init__(self, data: dict):
        self.code = data['code']
        self.icon = data['icon']
        self.day_text = data['day']['text']
        self.day_emoji = data['day']['emoji']
        self.night_text = data['night']['text']
        self.night_emoji = data['night']['emoji']

    def get_text(self, is_day: bool) -> str:
        return self.day_text if is_day else self.night_text

    def get_emoji(self, is_day: bool) -> str:
        return self.day_emoji if is_day else self.night_emoji


class DataLoader:
    def __init__(self):
        self.city_models = dict()
        self.weather_conditions = dict()

    def load(self):
        self.parse_city_models()
        self.parse_weather_conditions()

    def parse_city_models(self):
        file = open('data/cities.json', 'r', encoding='UTF-8')
        raw_json = '\n'.join(file.readlines())
        file.close()

        parsed: dict = json.loads(raw_json)
        for item in parsed.items():
            city = CityModel(item[0], item[1])
            self.city_models[city.city_id] = city

    def parse_weather_conditions(self):
        file = open('data/weather_conditions.json', 'r', encoding='UTF-8')
        raw_json = '\n'.join(file.readlines())
        file.close()

        parsed: list = json.loads(raw_json)
        for item in parsed:
            condition = WeatherCondition(item)
            self.weather_conditions[condition.code] = condition

    def get_city_model(self, _id: str) -> CityModel:
        return self.city_models[_id] if _id in self.city_models.keys() else None

    def get_weather_condition(self, _id: int) -> WeatherCondition | None:
        return self.weather_conditions[_id] if _id in self.weather_conditions.keys() else None
