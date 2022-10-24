from datetime import datetime
import aiohttp
import base64
import lat_lon_parser
from config import ASTRO_APP_ID, ASTRO_SECRET

api_url = 'https://api.astronomyapi.com/api/v2/bodies/positions'
auth_hash = base64.b64encode(f"{ASTRO_APP_ID}:{ASTRO_SECRET}".encode('utf-8')).decode('utf-8')

ru_obj_names = {'Moon': 'Луна', 'Sun': 'Солнце', 'Mercury': 'Меркурий', 'Venus': 'Венера', 'Mars': 'Марс',
                'Jupiter': 'Юпитер', 'Saturn': 'Сатурн', 'Uranus': 'Уран', 'Neptune': 'Нептун', 'Pluto': 'Плутон',
                'Earth': 'Земля'}

ru_phases = {'New Moon': '🌑 Новолуние', 'Waxing Crescent': '🌒 Молодая луна', 'First Quarter': '🌓 Первая Четверть',
             'Waxing Gibbous': '🌔 Прибывающая луна', 'Full Moon': '🌕 Полнолуние', 'Waning Gibbous': '🌖 Убывающая луна',
             'Last Quarter': '🌗 Последняя четверть', 'Waning Crescent': '🌘 Старая луна'}

ru_constellations = {'and': 'Андромеды', 'gem': 'Близнецов', 'uma': 'Большой Медведицы', 'cma': 'Большого Пса',
                     'lib': 'Весов', 'aqr': 'Водолея', 'aur': 'Возничего', 'lup': 'Волка', 'boo': 'Волопаса',
                     'com': 'Волос Вероники', 'crv': 'Ворона', 'her': 'Геркулеса', 'hya': 'Гидры', 'col': 'Голубя',
                     'cvn': 'Гончих Псов', 'vir': 'Девы', 'del': 'Дельфина', 'dra': 'Дракона', 'mon': 'Единорога',
                     'ara': 'Жертвенника', 'pic': 'Живописца', 'cam': 'Жирафа', 'gru': 'Журавля', 'lep': 'Зайца',
                     'oph': 'Змееносца', 'ser': 'Змеи', 'dor': 'Золотой Рыбы', 'ind': 'Индейца', 'cas': 'Кассиопеи',
                     'car': 'Киля', 'cet': 'Кита', 'cap': 'Козерога', 'pyx': 'Компаса', 'pup': 'Кормы', 'cyg': 'Лебедя',
                     'leo': 'Льва', 'vol': 'Летучей Рыбы', 'lyr': 'Лираы', 'vul': 'Лисички', 'umi': 'Малой Медведицы',
                     'equ': 'Малого Коня', 'lmi': 'Малого Льва', 'cmi': 'Малого Пса', 'mic': 'Микроскопа',
                     'mus': 'Мухи', 'ant': 'Насоса', 'nor': 'Наугольника', 'ari': 'Овна', 'oct': 'Октанта',
                     'aql': 'Орла', 'ori': 'Ориона', 'pav': 'Павлина', 'vel': 'Парусов', 'peg': 'Пегаса',
                     'per': 'Персея', 'for': 'Печи', 'aps': 'Райской Птицы', 'cnc': 'Рака', 'cae': 'Резца',
                     'psc': 'Рыб', 'lyn': 'Рыси', 'crb': 'Северной Короны', 'sex': 'Секстанта', 'ret': 'Сетки',
                     'sco': 'Скорпиона', 'scl': 'Скульптора', 'men': 'Столовой Горы', 'sge': 'Стрелы',
                     'sgr': 'Стрельца', 'tel': 'Телескопа', 'tau': 'Тельца', 'tri': 'Треугольника', 'tuc': 'Тукана',
                     'phe': 'Феникса', 'cha': 'Хамелеона', 'cen': 'Центавра', 'cep': 'Цефея', 'cir': 'Циркуля',
                     'hor': 'Часов', 'crt': 'Чаши', 'sct': 'Щита', 'eri': 'Эридана', 'hyi': 'Южной Гидры',
                     'cra': 'Южной Короны', 'psa': 'Южной Рыбы', 'cru': 'Южного Креста', 'tra': 'Южного Треугольника',
                     'lac': 'Ящерицы'}


def direction(angle: str) -> str:
    """Переводит угол азимута в словестное описание направления"""
    deg = int(angle.split('°')[0])
    for diection in ((22.5, "севере"), (67.5, "северо-востоке"), (112.5, "востоке"), (157.5, "юго-востоке"),
                     (202.5, "юге"), (247.50, "юго-западе"), (292.50, "западе"), (337.50, "северо-западе")):
        if deg <= diection[0]:
            return diection[1]
    return "севере"


async def get_astro_data(lat: str, lon :str, obs_time: datetime) -> str:
    """Делаем запрос на API astronomyapi.com"""
    params = {
        'longitude': lon,
        'latitude': lat,
        'elevation': '227',
        'from_date': obs_time.strftime("%Y-%m-%d"),
        'to_date': obs_time.strftime("%Y-%m-%d"),
        'time': obs_time.strftime("%H:%M:%S"),
    }
    headers = {'Authorization': f"Basic {auth_hash}"}

    async with aiohttp.ClientSession() as session:
        async with session.get(api_url, headers=headers, params=params) as resp:
            data = await resp.json()
            return parse_astro_data(data)


def parse_astro_data(data: dict) -> str:
    """Парсим json-ответ от API astronomyapi.com"""
    summary = []
    for x in data['data']['table']['rows']:
        planet_name = x['cells'][0]['name']
        elongation = x['cells'][0]['extraInfo']['elongation']
        try:
            magnitude = round(float(x['cells'][0]['extraInfo']['magnitude']), 2)
        except TypeError as ex:
            # print(ex)
            magnitude = None
        constellation = x['cells'][0]['position']['constellation'][
            'id']  # name можно заменить на id для трехбуквенных обозначений
        r_ascention = x['cells'][0]['position']['equatorial']['rightAscension']['string']  # or hours
        declination = x['cells'][0]['position']['equatorial']['declination']['string']  # or degrees
        altitude = x['cells'][0]['position']['horizonal']['altitude']['string']  # or degrees
        azimuth = x['cells'][0]['position']['horizonal']['azimuth']['string']  # or degrees

        list_item = f"{ru_obj_names[planet_name].upper()}\n"
        if planet_name == 'Moon':
            phase = ru_phases[x['cells'][0]['extraInfo']['phase']['string']]
            list_item += f"{phase}\n"
        list_item += f"находится в созвездии {ru_constellations[constellation]} и имеет яркость {magnitude} з.в.\n" \
            f"высота над горизонтом {altitude}\n" \
            f"азимут {azimuth} (на {direction(azimuth)})\n"

        if planet_name in ('Mercury', 'Venus'):
            list_item += f"элонгация {round(float(elongation), 1)}°\n"
        # list_item += f"прямое восхождение {r_ascention}\ncклонение {declination}\n"
        if lat_lon_parser.parse(altitude) > 5:
            summary.append(list_item)
    return '\n'.join(summary)
