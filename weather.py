from datetime import datetime
from data import DataLoader, CityModel
from time import sleep
from threading import Thread

import requests


class CityWeatherData:
    date_time: datetime
    temp_c: float
    temp_f: float
    feelslike_c: float
    feelslike_f: float
    weather_icon_id: int

    @staticmethod
    def from_response(response: dict):
        data: CityWeatherData = CityWeatherData()
        return data


class WeatherFetchThread(Thread):
    def __init__(self, bot):
        super().__init__(name="Weather Fetch Thread")
        self.bot = bot

    def run(self) -> None:
        while True:
            print('Fetching weather data...')
            self.tick()
            sleep(10)

    def tick(self):
        data_loader: DataLoader = self.bot.data_loader

        for city_model in data_loader.city_models.items():
            city_id: str = city_model[0]
            city: CityModel = city_model[1]

            self.perform_request(f'{city.raw_lat},{city.raw_lon}')

    def perform_request(self, query: str) -> CityWeatherData:
        url = f'https://api.weatherapi.com/v1/current.json'

        params = dict()
        params['key'] = self.bot.weather_api_key
        params['q'] = query

        headers = dict()
        headers['User-Agent'] = 'Traveller Conductor Weather Service'

        response = requests.get(url, params=params, headers=headers)
        # TODO: handle non 200 codes

        raw = response.json()
        weather_data = raw['current']

        return CityWeatherData.from_response(weather_data)
