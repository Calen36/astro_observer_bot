import json
from db import sync_get_banned


with open('secr.json', 'r') as file:
    secr = json.load(file)

TG_TOKEN = secr['TG_TOKEN']
DEV_TG_ID = secr['DEV_TG_ID']
WEATHER_ID = secr['WEATHER_ID']
ASTRO_SECRET = secr['ASTRO_SECRET']
ASTRO_APP_ID = secr['ASTRO_APP_ID']
NASA_KEY = secr['NASA_KEY']
YANDEX_GEO_TOKEN = secr['YANDEX_GEO_TOKEN']

BANLIST = sync_get_banned()


