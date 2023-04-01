import json
import random

from telegram import InlineKeyboardButton


class CityPhoto:
    def __init__(self, data: dict):
        self.tg_id = data['tg_id']
        self.file = data['file']
        self.source = data['source']


class CityModel:
    def __init__(self, city_id: str, data: dict):
        self.city_id: str = city_id
        self.name: str = data['name']
        self.country: str = data['country']
        self.emoji: str = data['emoji']
        self.latitude: str = data['latitude']
        self.longitude: str = data['longitude']
        self.raw_lat: float = data['lat']
        self.raw_lon: float = data['lon']
        self.area: float = data['area']
        self.population: str = data['population']
        self.time_offset: int = data['time_offset']
        self.photos: list = list()

        if 'photos' in data.keys():
            for item in data['photos']:
                self.photos.append(CityPhoto(item))

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
        self.user_photo_reactions = list()

    def load(self):
        self.parse_city_models()
        self.parse_weather_conditions()
        self.read_user_photo_reactions()

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

    def read_user_photo_reactions(self):
        file = open('data/phrases.txt', 'r', encoding='UTF-8')

        for line in file.readlines():
            line = line.rstrip('\n')
            if len(line) > 1:
                self.user_photo_reactions.append(line)

        file.close()

    def get_city_model(self, _id: str) -> CityModel:
        return self.city_models[_id] if _id in self.city_models.keys() else None

    def get_weather_condition(self, _id: int) -> WeatherCondition:
        return self.weather_conditions[_id] if _id in self.weather_conditions.keys() else None

    def get_random_photo_reaction(self) -> str:
        index = random.randint(0, len(self.user_photo_reactions) - 1)
        return self.user_photo_reactions[index]
