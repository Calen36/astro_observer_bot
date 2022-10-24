import datetime

import pytz
from tzwhere import tzwhere
import aiohttp
from config import YANDEX_GEO_TOKEN


def get_timezone_offset(lat: str | float, long: str | float) -> datetime.timedelta:
    """По координатам получаем сдвиг Часового пояся относительно UTC"""
    timezone_str = tzwhere.tzwhere().tzNameAt(lat, long)
    timezone = pytz.timezone(timezone_str)
    return timezone.utcoffset(datetime.datetime.now())


async def get_geodata(string: str) -> tuple[str, str, str]:
    """Обращается к API геокодирования Яндекса - по строке определяется адрес и координаты"""
    async with aiohttp.ClientSession() as session:
        yandex_geocoder_url = 'https://geocode-maps.yandex.ru/1.x/'
        params = {'apikey': YANDEX_GEO_TOKEN, 'format': 'json', 'geocode': string}
        async with session.get(url=yandex_geocoder_url, params=params) as resp:
            result = await resp.json(encoding='utf8')
        try:
            descr = result['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['metaDataProperty']['GeocoderMetaData']['text']
            print(descr)
            coord = result['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['Point']['pos']
            print(coord)        
            long, lat = coord.split()
            return descr, lat, long
        except Exception as ex:
            print('Ошибка при обращении к api Яндекса:', ex)
