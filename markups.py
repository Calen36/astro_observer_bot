from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

main_kbd = ReplyKeyboardMarkup(resize_keyboard=True)  # one_time_keyboard=True
b1 = KeyboardButton('Местоположение')
b2 = KeyboardButton('Cейчас')
b3 = KeyboardButton('Вечер')
b4 = KeyboardButton('Полночь')
b5 = KeyboardButton('Утро')
b6 = KeyboardButton('Задать время')

b11 = KeyboardButton('Погода сейчас')
b12 = KeyboardButton('Планеты')
main_kbd.row(b3, b4, b5).row(b1, b6, b2)  # .add(b).insert(b).row(b)

place_kbd = InlineKeyboardMarkup(row_width=3)
ib1 = InlineKeyboardButton(text='Получить с уcтройства', callback_data='get_coords')
ib2 = InlineKeyboardButton(text='Ввести название', callback_data='input_place')
ib3 = InlineKeyboardButton(text='Отмена', callback_data='cancel_coords')
place_kbd.row(ib1, ib2, ib3)

location_kbd = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
lb1 = KeyboardButton('Получить с устройства', request_location=True)
lb2 = KeyboardButton('Ввести местоположение')
lb3 = KeyboardButton('Отмена')
location_kbd.row(lb1, lb2, lb3)
