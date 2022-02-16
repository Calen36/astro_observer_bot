from config import DEV_CHAT_ID
from aiogram import types
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from astrobot import bot, dp
from markups import main_kbd, location_kbd
from db import get_users, get_user, update_user
from geo_api import get_geodata
from weather_api import fetch_current_weather, fetch_forecast, ru_month
from astro_api import get_astro_data
from nasa_api import get_apod

import lat_lon_parser
from datetime import datetime, timedelta


class PlaceNameFSM(StatesGroup):
    namestring = State()


class TimeFSM(StatesGroup):
    time_needed = State()


async def start_cmd(message: types.Message):
    msg = "Привет! Я - бот-помощник астронома-любителя.\n\nЯ умею показывать погоду и объекты солнечной системы," \
          " доступные для наблюденя сейчас, ближайшей ночью (вечером через час после заката, в середине ночи, и утром" \
          " за час до восхода), либо в указанное время. Чтобы начать работу - задайте местоположение наблюдения.\n\n" \
          "PS: А еще вы можете попросить бота показать картинку)\n\nPPS: Если вы хотите-что передать разработчику " \
          "(например, если багу изловили) - начните сообщение с букв DEV"
    await bot.send_message(message.from_user.id, msg, reply_markup=main_kbd) #  reply_markup=kb_client,


async def place_cmd(message: types.Message):
    userinfo = await get_user(message.from_user.id)
    if userinfo:
        name = f"\n({userinfo[3]})" if userinfo[3] else ""
        header = f'Выбранное местоположение:\nШирота {userinfo[1]}, Долгота {userinfo[2]}{name}\n\nВы можете изменить'
    else:
        header = 'В данный момент местоположение не выбрано.\n\nВы можете задать'
    msg = f'{header} его вручную или передав координаты со своего устройства.'
    await bot.send_message(message.from_user.id, msg, reply_markup=location_kbd)


async def cancel(message: types.Message):
    await bot.send_message(message.from_user.id, 'ок', reply_markup=main_kbd)


async def catch_location(message: types.Message):
    lat = message.location.latitude
    lon = message.location.longitude
    await update_user(message.from_user.id, str(lat), str(lon))
    reply = f"Установлены коордитнаты:\nШирота {lat}\nДолгота {lon}"
    await message.answer(reply, reply_markup=main_kbd)


async def prepare_latlon_input(message: types.Message):
    await PlaceNameFSM.namestring.set()
    await message.answer('Введите название населенного пункта или значения широты и долготы, разделенные пробелом:')


async def input_latlon(message: types.Message, state=FSMContext):
    result = await get_geodata(message.text)
    if all(result):
        reply = f"Установлено местоположение:\n{result[0]}\nШирота {result[1]}\nДолгота {result[2]}"
        await update_user(message.from_user.id, result[1], result[2], result[0])
        await message.reply(reply, reply_markup=main_kbd)
    else:
        msg = message.text.split()
        part1, part2 = ' '.join(msg[:len(msg)//2]), ' '.join(msg[len(msg)//2:])
        try:
            lat = lat_lon_parser.parse(part1)
            lon = lat_lon_parser.parse(part2)
            await update_user(message.from_user.id, lat, lon)
            reply = f"Установлено местоположение:\nШирота {lat}\nДолгота {lon}"
        except ValueError:
            reply = '🤷 Ничего не понимаю!'
        await message.reply(reply, reply_markup=location_kbd)
    await state.finish()


async def get_curr_weather(message):
    userdata = await get_user(message.from_user.id)
    if userdata and all(userdata[:3]):  # проверяем, что местоположение задано
        sunset, sunrise, msg = await fetch_current_weather(userdata[1], userdata[2])
        return sunset, sunrise, msg, userdata
    else:
        await message.answer('Сначала задайте местоположение', reply_markup=location_kbd)
        return None, None, None, None


async def send_status_init(message, userdata, obs_time):
    name = f", ({userdata[3]})" if userdata[3] else ''
    date = f"{obs_time.strftime('%d')} {ru_month[obs_time.strftime('%m')]} {obs_time.strftime('%Y')}"
    await message.answer(f"Данные для: {userdata[1]}, {userdata[2]}{name}\n{date} в {obs_time.strftime('%H:%M')}", reply_markup=main_kbd)


async def status_now(message: types.Message):
    sunset, sunrise, weather_msg, userdata = await get_curr_weather(message)
    if weather_msg:
        obs_time = datetime.now()
        await send_status_init(message, userdata, obs_time)
        await message.answer(weather_msg, reply_markup=main_kbd)
        solar_sys = await get_astro_data(lat=userdata[1], lon=userdata[2], obs_time=obs_time)
        await message.answer(solar_sys, reply_markup=main_kbd)


async def status_evening(message: types.Message):
    sunset, sunrise, _, userdata = await get_curr_weather(message)
    now = datetime.now()
    if sunset:
        obs_time = sunset + timedelta(hours=1)
        if now - timedelta(hours=3) > obs_time:
            obs_time += timedelta(days=1)
        await send_status_init(message, userdata, obs_time)
        forecast_msg = await fetch_forecast(userdata[1], userdata[2], obs_time)
        await message.answer(forecast_msg, reply_markup=main_kbd)
        solar_sys = await get_astro_data(lat=userdata[1], lon=userdata[2], obs_time=obs_time)
        await message.answer(solar_sys, reply_markup=main_kbd)


async def status_midnight(message: types.Message):
    sunset, sunrise, _, userdata = await get_curr_weather(message)
    now = datetime.now()
    if sunset:
        sunset_h = int(sunset.strftime("%H"))
        sunset_m = int(sunset.strftime("%M"))
        sunrise_h = int(sunrise.strftime("%H"))
        sunrise_m = int(sunrise.strftime("%M"))
        delta = ((sunrise_h + 24 - sunset_h) * 60 + sunrise_m - sunset_m) // 2  # кол-во минут от заката до середины ночи
        obs_time = sunset + timedelta(minutes=delta)
        if now - timedelta(hours=3) > obs_time:
            obs_time += timedelta(days=1)
        await send_status_init(message, userdata, obs_time)
        forecast_msg = await fetch_forecast(userdata[1], userdata[2], obs_time)
        await message.answer(forecast_msg, reply_markup=main_kbd)
        solar_sys = await get_astro_data(lat=userdata[1], lon=userdata[2], obs_time=obs_time)
        await message.answer(solar_sys, reply_markup=main_kbd)


async def status_morning(message: types.Message):
    sunset, sunrise, _, userdata = await get_curr_weather(message)
    if sunrise:
        now = datetime.now()
        obs_time = sunrise - timedelta(hours=1)
        if now - timedelta(hours=3) > obs_time:
            obs_time += timedelta(days=1)
        await send_status_init(message, userdata, obs_time)
        forecast_msg = await fetch_forecast(userdata[1], userdata[2], obs_time)
        await message.answer(forecast_msg, reply_markup=main_kbd)
        solar_sys = await get_astro_data(lat=userdata[1], lon=userdata[2], obs_time=obs_time)
        await message.answer(solar_sys, reply_markup=main_kbd)


async def prepare_time_input(message: types.Message):
    await TimeFSM.time_needed.set()
    await message.answer('Введите дату и время в формате "ДД ММ ГГГГ ЧЧ мм"\n(прогноз погоды выводиться не будет)')


async def input_time(message: types.Message, state=FSMContext):
    await state.finish()
    try:
        obs_time = datetime.strptime(message.text.strip(), "%d %m %Y %H %M")
        await message.answer(obs_time)

        sunset, sunrise, weather_msg, userdata = await get_curr_weather(message)
        if weather_msg:
            await send_status_init(message, userdata, obs_time)
            solar_sys = await get_astro_data(lat=userdata[1], lon=userdata[2], obs_time=obs_time)
            await message.answer(solar_sys, reply_markup=main_kbd)
    except Exception as ex:
        print(f'Ошибка во время ввода времени: {ex}')
        await message.answer('🤷 Ничего не понимаю!')
        return


async def show_apod(message: types.Message):
    title, apod_url = await get_apod()
    await message.answer(f"{apod_url}\n{title}")


async def contact_dev(message: types.Message):
    await message.reply(f"Ок, я передам")
    await message.forward(chat_id=DEV_CHAT_ID)


async def test(message: types.Message):
    result = await get_user(message.from_user.id)
    print(result)
    apod_url = await get_apod()
    apod_url+= '\nабракадабра'
    await message.answer(apod_url)
