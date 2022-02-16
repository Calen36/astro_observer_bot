from config import NASA_KEY
import aiohttp
from random import randint
from datetime import datetime


async def get_apod(random=True):
    if random:
        now = datetime.now()
        curr_year = int(now.strftime("%Y"))
        curr_month = int(now.strftime("%m"))
        curr_day = int(now.strftime("%d"))
        year = randint(2015, curr_year)
        maxmonth = curr_month if year == curr_year else 12
        month = randint(1, maxmonth)
        num_days = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
        maxday = curr_day if year == curr_year and month == curr_month else num_days[month-1]
        day = randint(1, maxday)
        date = f"{year}-{month}-{day}"
        params = {"api_key": NASA_KEY, "date": date}
    else:
        params = {"api_key": NASA_KEY}
    api_url = "https://api.nasa.gov/planetary/apod"
    async with aiohttp.ClientSession() as session:
        async with session.get(api_url, params=params) as resp:
            data = await resp.json()
            if 'url' in data and 'title' in data:  # если чего-то не хаватает - выводим картинку за сегодня
                title, url = data['title'], data['url']
            elif data['media type'] != 'image':
                title, url = get_apod()
            else:
                title, url = await get_apod(random=False)
            return title, url
