import json
from datetime import datetime, timedelta
from config import WEATHER_ID
import aiohttp


ru_month = {'01': 'января', '02': 'февраля', '03': 'марта', '04': 'апреля', '05': 'мая', '06': 'июня', '07': 'июля',
              '08': 'августа', '09': 'сентября', '10': 'октября', '11': 'ноября', '12': 'декабря'}


def wind_dir(deg):
    for diection in ((22.5, "южный "), (67.5, "юго-западный "), (112.5, "западный "), (157.5, "северо-западный "),
                     (202.5, "северный "), (247.50, "северо-восточный "), (292.50, "восточный "), (337.50, "юго-восточный ")):
        if deg <= diection[0]:
            return diection[1]
    return "южный "


def get_cloudiness(percent):
    for state in ((2, "ясно"), (25, "малооблачно"), (50, "рассеянная облачность"),
                  (75, "облчачно с прояснениями"), (98, 'облачно')):
        if percent < state[0]:
            return state[1]
    return "сплошная облачность"


def rainfall(mm):
    for amount in ((0.01, f"без существенных осадков ({mm} за час)"), (0.033, f"небольшой дождь ({mm} за час)"), (1.25, f"дождь ({mm} за час)"), (4.17, f"сильный дождь ({mm} за час)")):
        if mm < amount[0]:
            return amount[1]
    return f"очень сильный дождь ({mm} за час)"


def snowfall(mm):
    for amount in ((0.003, f"без существенных осадков ({mm} за час)"), (0.17, f"небольшой снег ({mm} за час)"), (0.5, f"снег ({mm} за час)"), (1.6, f"сильный снег ({mm} за час)")):
        if mm < amount[0]:
            return amount[1]
    return f"очень сильный снег ({mm} за час)"


def get_precip(rain, snow):
    if rain == snow == 0:
        return "без осадков"
    if rain == 0:
        return snowfall(snow)
    if snow == 0:
        return rainfall(rain)
    mm = rain + snow
    for amount in ((0.01, f"без существенных осадков ({mm} за час)"), (0.03, f"небольшой дождь со снегом ({mm} за час)"),
                   (1.15, f"дождь со снегом ({mm} за час)"), (4, f"сильный дождь со снегом ({mm} за час)")):
        if mm < amount[0]:
            return amount[1]
    return f"очень сильный дождь со снегом ({mm} за час)"


async def fetch_current_weather(lat, lon):
    api_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        'lat': lat,
        'lon': lon,
        'appid': WEATHER_ID,
        'units': 'metric',
        'lang': 'ru'
    }

    async with aiohttp.ClientSession() as session:

        async with session.get(api_url, params=params) as resp:
            data = await resp.json()
            sunrise = datetime.utcfromtimestamp(data['sys']['sunrise'] + 10800)
            sunset = datetime.utcfromtimestamp(data['sys']['sunset'] + 10800)
            weather = data['weather'][0]['description']
            temp = round(data['main']['temp'], 1)
            pressure = round(data['main']['pressure']*0.75)
            humid = data['main']['humidity']
            visib = data['visibility']
            wind = round(data['wind']['speed'])
            deg = data['wind']['deg']
            w_dir = wind_dir(deg)
            clouds = data['clouds']['all']
            cloudiness = get_cloudiness(clouds)
            rain = data["rain"]["1h"] if "rain" in data.keys() else 0
            snow = data["snow"]["1h"] if "snow" in data.keys() else 0
            precip = get_precip(rain, snow)

            msg = f"Закат в {sunset.strftime('%H:%M')}, восход в {sunrise.strftime('%H:%M')}\n{weather.capitalize()}, " \
                  f"{precip}\nТемпература: {temp} ℃\nДавление: {pressure} мм рт. ст.\nВлажность: {humid} %\n" \
                  f"Видимость {visib} м\nВетер {w_dir}{wind} м/с\nОблачность {clouds}%\n"
            return sunset, sunrise, msg


async def fetch_forecast(lat, lon, time):
    api_url = "http://api.openweathermap.org/data/2.5/forecast"
    params = {
        'lat': lat,
        'lon': lon,
        'appid': WEATHER_ID,
        'units': 'metric',
        'lang': 'ru'
    }

    async with aiohttp.ClientSession() as session:

        async with session.get(api_url, params=params) as resp:
            forecasts = await resp.json()
            for data in forecasts['list']:
                forecast_time = datetime.strptime(data['dt_txt'], "%Y-%m-%d %H:%M:%S")
                if max(time, forecast_time) - min(time, forecast_time) < timedelta(minutes=91):
                    # print(json.dumps(data, indent=4))
                    weather = data['weather'][0]['description']
                    temp = round(data['main']['temp'], 1)
                    pressure = round(data['main']['pressure']*0.75)
                    humid = data['main']['humidity']
                    visib = data['visibility']
                    wind = round(data['wind']['speed'])
                    deg = data['wind']['deg']
                    w_dir = wind_dir(deg)
                    clouds = data['clouds']['all']
                    cloudiness = get_cloudiness(clouds)
                    try:
                        rain = data["rain"]["1h"]
                    except KeyError:
                        try:
                            rain = data["rain"]["3h"] / 3
                        except KeyError:
                            rain = 0
                    try:
                        snow = data["snow"]["1h"]
                    except KeyError:
                        try:
                            snow = data["snow"]["3h"] / 3
                        except KeyError:
                            snow = 0

                    precip = get_precip(rain, snow)
                    time = data['dt_txt']

                    msg = f"{weather.capitalize()}, {precip}\nТемпература: {temp} ℃\nДавление: {pressure}" \
                          f" мм рт. ст.\nВлажность: {humid} %\nВидимость {visib} м\nВетер {w_dir}{wind}" \
                          f" м/с\nОблачность {clouds}%\n"
                    return msg
