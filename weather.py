from datetime import datetime
from threading import Thread
from time import sleep

from requests import get, ConnectionError

from data import DataLoader, CityModel


# Модель данных, описывающая сохранённую текущую погоду в городе
# Используется для хранения погоды в памяти и обновляется в фоне
class CityWeatherData:
    date_time: datetime
    temp_c: float
    temp_f: float
    feelslike_c: float
    feelslike_f: float
    humidity: int
    cloud: int
    is_day: bool
    condition_code: int

    def __init__(self):
        super().__init__()

    def load_from_response(self, weather_data: dict):
        self.date_time = datetime.fromtimestamp(weather_data['last_updated_epoch'])
        self.temp_c = weather_data['temp_c']
        self.temp_f = weather_data['temp_f']
        self.feelslike_c = weather_data['feelslike_c']
        self.feelslike_f = weather_data['feelslike_f']
        self.humidity = weather_data['humidity']
        self.cloud = weather_data['cloud']
        self.is_day = weather_data['is_day'] == 1
        self.condition_code = weather_data['condition']['code']
        return self


# Класс, реализующий сервис погоды, который контролирует
# сохранение данных в памяти и их фоновое обновление
class WeatherService:
    def __init__(self, bot):
        self.bot = bot
        self.thread = WeatherFetchThread(self)
        self.cache = dict()

    def get_cached_weather_data(self, city_id: str) -> CityWeatherData:
        return self.cache[city_id] if city_id in self.cache.keys() else None

    def update_weather_data(self, city_id: str, data):
        self.cache[city_id] = data

    def start(self):
        self.thread.start()


# Облегчённая модель города, содержащая только географические координаты
# города, необходимые для точных запросов погоды от WeatherAPI
class QueryItem:
    def __init__(self, city_id: str, city: CityModel):
        self.city_id = city_id
        self.lat = city.raw_lat
        self.lon = city.raw_lon

    def query_string(self) -> str:
        return f'{self.lat},{self.lon}'


# Реализация потока, выполняющего функцию обновления информации о погоде
# в фоновом режиме, работая со списком моделей QueryItems, получая
# информацию о погоде в виде CityWeatherData и сохраняя её в памяти
class WeatherFetchThread(Thread):
    def __init__(self, service: WeatherService):
        super().__init__(name="Weather Fetch Thread", daemon=True)
        self.service = service
        self.query_items = list()

        data_loader: DataLoader = service.bot.data_loader
        for city_model in data_loader.city_models.items():
            self.query_items.append(QueryItem(city_model[0], city_model[1]))

    # Циклический вызов #tick()
    # Интервал необходим для соблюдения ограничения частоты запросов к WeatherAPI
    def run(self) -> None:
        while True:
            try:
                self.tick()
            except ConnectionError:
                print("[Weather Service] Connection error :(")
            sleep(10)

    # Вызов #perform_request(str) и обновление данных в памяти
    def tick(self):
        for query_item in self.query_items:
            data = self.perform_request(query_item.query_string())
            self.service.update_weather_data(query_item.city_id, data)
            sleep(10)

    # Выполнение HTTP запроса к WeatherAPI с ключом 'q' (query)
    def perform_request(self, query: str):
        url = 'https://api.weatherapi.com/v1/current.json'

        params = dict()
        params['key'] = self.service.bot.weather_api_key
        params['q'] = query

        headers = dict()
        headers['User-Agent'] = 'Traveller Conductor Weather Service'

        response = get(url, params=params, headers=headers)
        if response.status_code != 200:
            print(f"Status code {response.status_code} received when I tried to query weather status for '{query}' :(")
            return None

        raw = response.json()
        weather_data = raw['current']

        return CityWeatherData().load_from_response(weather_data)
