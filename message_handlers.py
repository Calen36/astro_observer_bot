from config import DEV_CHAT_ID, BANLIST
from aiogram import types
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from astrobot import bot, dp
from markups import main_kbd, location_kbd
from geo_api import get_geodata
from weather_api import fetch_current_weather, fetch_forecast, ru_month
from astro_api import get_astro_data
from nasa_api import get_apod
from db import get_users, get_user, update_user, get_uid, ban_user, unban_user, get_banned

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
          "PS: А еще вы можете попросить меня показать картинку)\n\nPPS: Если вы хотите-что передать разработчику " \
          "(например, если багу изловили) - начните сообщение с букв DEV"
    await bot.send_message(message.from_user.id, msg, reply_markup=main_kbd) #  reply_markup=kb_client,


async def place_cmd(message: types.Message):
    """Choose location menu"""
    userinfo = await get_user(message.from_user.id)
    if userinfo:
        place = f"\n({userinfo[3]})" if userinfo[3] else ""
        header = f'Выбранное местоположение:\nШирота {userinfo[1]}, Долгота {userinfo[2]}{place}\n\nВы можете изменить'
    else:
        header = 'В данный момент местоположение не выбрано.\n\nВы можете задать'
    msg = f'{header} его вручную или передав координаты со своего устройства.'
    await bot.send_message(message.from_user.id, msg, reply_markup=location_kbd)


async def cancel(message: types.Message):
    """Cancels location choosing, returns main keyboard"""
    await bot.send_message(message.from_user.id, 'ок', reply_markup=main_kbd)


async def catch_location(message: types.Message):
    """Procces location data from user device"""
    lat = message.location.latitude
    lon = message.location.longitude
    try:
        username = message.from_user['username']
    except KeyError:
        username = ''
    await update_user(message.from_user.id, str(lat), str(lon), name=username)
    reply = f"Установлены коордитнаты:\nШирота {lat}\nДолгота {lon}"
    await message.answer(reply, reply_markup=main_kbd)


async def prepare_latlon_input(message: types.Message):
    await PlaceNameFSM.namestring.set()
    await message.answer('Введите название населенного пункта или значения широты и долготы, разделенные пробелом:')


async def input_latlon(message: types.Message, state=FSMContext):
    """Parces inputed location"""
    result = await get_geodata(message.text)
    try:
        username = message.from_user['username']
    except KeyError:
        username = ''

    if all(result):
        reply = f"Установлено местоположение:\n{result[0]}\nШирота {result[1]}\nДолгота {result[2]}"
        await update_user(message.from_user.id, result[1], result[2], result[0], username)
        await message.reply(reply, reply_markup=main_kbd)
    else:
        msg = message.text.split()
        part1, part2 = ' '.join(msg[:len(msg)//2]), ' '.join(msg[len(msg)//2:])
        try:
            lat = lat_lon_parser.parse(part1)
            lon = lat_lon_parser.parse(part2)
            await update_user(message.from_user.id, lat, lon, username)
            reply = f"Установлено местоположение:\nШирота {lat}\nДолгота {lon}"
        except ValueError:
            reply = '🤷 Ничего не понимаю!'
        await message.reply(reply, reply_markup=location_kbd)
    await state.finish()


async def get_curr_weather(message):
    """Gets current weather and local time from api"""
    userdata = await get_user(message.from_user.id)
    if userdata and all(userdata[:3]):  # проверяем, что местоположение задано
        sunset, sunrise, localnow, msg = await fetch_current_weather(userdata[1], userdata[2])
        return sunset, sunrise, localnow, msg, userdata
    else:
        await message.answer('Сначала задайте местоположение', reply_markup=location_kbd)
        return None, None, None, None, None


async def send_status_init(message, userdata, obs_time):
    """Sends first message in bot's main response"""
    name = f", ({userdata[3]})" if userdata[3] else ''
    date = f"{obs_time.strftime('%d')} {ru_month[obs_time.strftime('%m')]} {obs_time.strftime('%Y')}"
    await message.answer(f"Данные для: {userdata[1]}, {userdata[2]}{name}\n{date} в {obs_time.strftime('%H:%M')}", reply_markup=main_kbd)


async def status_now(message: types.Message):
    """Sends 2 messages: current weather and solar system objects visible now"""
    sunset, sunrise, obs_time, weather_msg, userdata = await get_curr_weather(message)
    if weather_msg:
        await send_status_init(message, userdata, obs_time)
        await message.answer(weather_msg, reply_markup=main_kbd)
        solar_sys = await get_astro_data(lat=userdata[1], lon=userdata[2], obs_time=obs_time)
        await message.answer(solar_sys, reply_markup=main_kbd)


async def status_evening(message: types.Message):
    """Sends 2 messages: weather at the start of night and solar system objects visible at that time"""
    sunset, sunrise, localnow, _, userdata = await get_curr_weather(message)
    if sunset:
        obs_time = sunset + timedelta(hours=1)
        if localnow - timedelta(hours=3) > obs_time:
            obs_time += timedelta(days=1)
        await send_status_init(message, userdata, obs_time)
        forecast_msg = await fetch_forecast(userdata[1], userdata[2], obs_time)
        try:
            await message.answer(forecast_msg, reply_markup=main_kbd)
        except Exception as ex:
            print(ex)
        solar_sys = await get_astro_data(lat=userdata[1], lon=userdata[2], obs_time=obs_time)
        await message.answer(solar_sys, reply_markup=main_kbd)


async def status_midnight(message: types.Message):
    """Sends 2 messages: weather at midnight and solar system objects visible at that time"""
    sunset, sunrise, localnow, _, userdata = await get_curr_weather(message)
    if sunset:
        sunset_h = int(sunset.strftime("%H"))
        sunset_m = int(sunset.strftime("%M"))
        sunrise_h = int(sunrise.strftime("%H"))
        sunrise_m = int(sunrise.strftime("%M"))
        delta = ((sunrise_h + 24 - sunset_h) * 60 + sunrise_m - sunset_m) // 2  # кол-во минут от заката до середины ночи
        obs_time = sunset + timedelta(minutes=delta)
        if localnow - timedelta(hours=3) > obs_time:
            obs_time += timedelta(days=1)
        await send_status_init(message, userdata, obs_time)
        forecast_msg = await fetch_forecast(userdata[1], userdata[2], obs_time)
        await message.answer(forecast_msg, reply_markup=main_kbd)
        solar_sys = await get_astro_data(lat=userdata[1], lon=userdata[2], obs_time=obs_time)
        await message.answer(solar_sys, reply_markup=main_kbd)


async def status_morning(message: types.Message):
    """Sends 2 messages: weather at the end of night and solar system objects visible at that time"""
    sunset, sunrise, localnow, _, userdata = await get_curr_weather(message)
    if sunrise:
        obs_time = sunrise - timedelta(hours=1)
        if localnow - timedelta(hours=3) > obs_time:
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
    """Parse time input and sends sends message with solar system objects visible at that time"""
    await state.finish()
    try:
        obs_time = datetime.strptime(message.text.strip(), "%d %m %Y %H %M")
        await message.answer(obs_time)

        sunset, sunrise, localnow, weather_msg, userdata = await get_curr_weather(message)
        if weather_msg:
            await send_status_init(message, userdata, obs_time)
            solar_sys = await get_astro_data(lat=userdata[1], lon=userdata[2], obs_time=obs_time)
            await message.answer(solar_sys, reply_markup=main_kbd)
    except Exception as ex:
        print(f'Ошибка во время ввода времени: {ex}')
        await message.answer('🤷 Ничего не понимаю!')
        return


async def show_apod(message: types.Message):
    """Sends link to astronomy picture of the day"""
    title, apod_url = await get_apod()
    await message.answer(f"{apod_url}\n{title}")


async def contact_dev(message: types.Message):
    """Forwards user's message to developer"""
    await message.reply(f"Ок, я передам")
    await message.forward(chat_id=DEV_CHAT_ID)
    
    
async def admin(message: types.Message):
    """Parce admin commands"""
    global BANLIST
    msg = message.text.split()
    if msg[0] == 'SEND':
        if msg[1].startswith('@'):
            uid = await get_uid(msg[1][1:])
            if uid:
                await bot.send_message(chat_id=uid, text=f"{' '.join(msg[2:])}")
                await message.reply('Отправлено.')
            else:
                await message.reply('пользователь не найден')
    elif msg[0] == 'BAN' and msg[1].startswith('@'):
        uid = await get_uid(msg[1][1:])
        if uid and uid != DEV_CHAT_ID:
            await ban_user(uid)
            BANLIST = await get_banned()
            await message.reply(f"{msg[1]} забанен")
        else:
            await message.reply(f"{msg[1]} не найден")
    elif msg[0] == 'UNBAN' and msg[1].startswith('@'):
        uid = await get_uid(msg[1][1:])
        if uid:
            await unban_user(uid)
            BANLIST = await get_banned()
            await message.reply(f"{msg[1]} разбанен")
        else:
            await message.reply(f"{msg[1]} не найден")


async def ban(message: types.Message):
    pass


async def test(message: types.Message):
    """Sandbox"""
    result = await get_user(message.from_user.id)
    print(result)
    apod_url = await get_apod()
    apod_url+= '\nабракадабра'
    await message.answer(apod_url)
