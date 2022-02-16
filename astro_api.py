import json
from datetime import datetime
import aiohttp
import base64
import lat_lon_parser
from config import *

api_url = 'https://api.astronomyapi.com/api/v2/bodies/positions'
auth_hash = base64.b64encode(f"{ASTRO_APP_ID}:{ASTRO_SECRET}".encode('utf-8')).decode('utf-8')

ru_obj_names = {'Moon': 'Луна', 'Sun': 'Солнце', 'Mercury': 'Меркурий', 'Venus': 'Венера', 'Mars': 'Марс',
                'Jupiter': 'Юпитер', 'Saturn': 'Сатурн', 'Uranus': 'Уран', 'Neptune': 'Нептун', 'Pluto': 'Плутон',
                'Earth': 'Земля'}

ru_phases = {'New Moon': '🌑 Новолуние', 'Waxing Crescent': '🌒 Молодая луна', 'First Quarter': '🌓 Первая Четверть',
             'Waxing Gibbous': '🌔 Прибывающая луна', 'Full Moon': '🌕 Полнолуние', 'Waning Gibbous': '🌖 Убывающая луна',
             'Last Quarter': '🌗 Последняя четверть', 'Waning Crescent': '🌘 Старая луна'}

ru_constellations = {'and': 'Андромеда', 'gem': 'Близнецы', 'uma': 'Большая Медведица', 'cma': 'Большой Пёс',
                     'lib': 'Весы', 'aqr': 'Водолей', 'aur': 'Возничий', 'lup': 'Волк', 'boo': 'Волопас',
                     'com': 'Волосы Вероники', 'crv': 'Ворон', 'her': 'Геркулес', 'hya': 'Гидра', 'col': 'Голубь',
                     'cvn': 'Гончие Псы', 'vir': 'Дева', 'del': 'Дельфин', 'dra': 'Дракон', 'mon': 'Единорог',
                     'ara': 'Жертвенник', 'pic': 'Живописец', 'cam': 'Жираф', 'gru': 'Журавль', 'lep': 'Заяц',
                     'oph': 'Змееносец', 'ser': 'Змея', 'dor': 'Золотая Рыба', 'ind': 'Индеец', 'cas': 'Кассиопея',
                     'car': 'Киль', 'cet': 'Кит', 'cap': 'Козерог', 'pyx': 'Компас', 'pup': 'Корма', 'cyg': 'Лебедь',
                     'leo': 'Лев', 'vol': 'Летучая Рыба', 'lyr': 'Лира', 'vul': 'Лисичка', 'umi': 'Малая Медведица',
                     'equ': 'Малый Конь', 'lmi': 'Малый Лев', 'cmi': 'Малый Пёс', 'mic': 'Микроскоп', 'mus': 'Муха',
                     'ant': 'Насос', 'nor': 'Наугольник', 'ari': 'Овен', 'oct': 'Октант', 'aql': 'Орёл', 'ori': 'Орион',
                     'pav': 'Павлин', 'vel': 'Паруса', 'peg': 'Пегас', 'per': 'Персей', 'for': 'Печь',
                     'aps': 'Райская Птица', 'cnc': 'Рак', 'cae': 'Резец', 'psc': 'Рыбы', 'lyn': 'Рысь',
                     'crb': 'Северная Корона', 'sex': 'Секстант', 'ret': 'Сетка', 'sco': 'Скорпион', 'scl': 'Скульптор',
                     'men': 'Столовая Гора', 'sge': 'Стрела', 'sgr': 'Стрелец', 'tel': 'Телескоп', 'tau': 'Телец',
                     'tri': 'Треугольник', 'tuc': 'Тукан', 'phe': 'Феникс', 'cha': 'Хамелеон', 'cen': 'Центавр',
                     'cep': 'Цефей', 'cir': 'Циркуль', 'hor': 'Часы', 'crt': 'Чаша', 'sct': 'Щит', 'eri': 'Эридан',
                     'hyi': 'Южная Гидра', 'cra': 'Южная Корона', 'psa': 'Южная Рыба', 'cru': 'Южный Крест',
                     'tra': 'Южный Треугольник', 'lac': 'Ящерица'}


def direction(angle):
    deg = int(angle.split('°')[0])
    for diection in ((22.5, "севере"), (67.5, "северо-востоке"), (112.5, "востоке"), (157.5, "юго-востоке"),
                     (202.5, "юге"), (247.50, "юго-западе"), (292.50, "западе"), (337.50, "северо-западе")):
        if deg <= diection[0]:
            return diection[1]
    return "севере"


async def get_astro_data(lat, lon, obs_time):
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
            # print(json.dumps(data, indent=4))
            return parse_astro_data(data)


def parse_astro_data(data):
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
