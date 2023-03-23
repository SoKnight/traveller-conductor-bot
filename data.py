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
        self.area = data['area']
        self.population = data['population']

    def as_inline_button(self):
        return InlineKeyboardButton(f'{self.emoji} {self.name}', callback_data=f'#select_city {self.city_id}')


class DataLoader:
    def __init__(self):
        self.city_models = dict()

    def load(self):
        self.parse_city_models()

    def parse_city_models(self):
        file = open('data/cities.json', 'r', encoding='UTF-8')
        raw_json = '\n'.join(file.readlines())
        file.close()

        parsed: dict = json.loads(raw_json)
        for item in parsed.items():
            model = CityModel(item[0], item[1])
            self.city_models[item[0]] = model

    def get_city_model(self, city_id: str) -> CityModel:
        return self.city_models[city_id]
