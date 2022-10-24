from aiogram.utils import executor
from aiogram.dispatcher.filters import Text, BoundFilter, IDFilter

from astrobot import dp
from message_handlers import *
from config import DEV_TG_ID, BANLIST


class Banned(BoundFilter):
    """Фильтр, не позволяющий забаненным пользоваться ботом"""
    key = 'is_banned'

    def __init__(self, is_banned):
        self.is_banned = is_banned

    async def check(self, message: types.Message):
        return message.chat.id in BANLIST


dp.filters_factory.bind(Banned)

dp.register_message_handler(do_nothing, is_banned=True)
# dp.register_message_handler(test, Text(equals='Тест', ignore_case=True))
dp.register_message_handler(prepare_latlon_input, Text(equals='Ввести местоположение', ignore_case=True))
dp.register_message_handler(input_latlon, state=PlaceNameFSM.namestring)
dp.register_message_handler(start_cmd, commands=['start', 'help'])
dp.register_message_handler(sys_cmd, commands=['status'])
dp.register_message_handler(place_cmd, Text(equals='Местоположение', ignore_case=True))
dp.register_message_handler(cancel, Text(equals='Отмена', ignore_case=True))
dp.register_message_handler(status_now, Text(equals='Cейчас', ignore_case=True))
dp.register_message_handler(status_evening, Text(equals='Вечер', ignore_case=True))
dp.register_message_handler(status_midnight, Text(equals='Полночь', ignore_case=True))
dp.register_message_handler(status_morning, Text(equals='Утро', ignore_case=True))
dp.register_message_handler(prepare_time_input, Text(equals='Задать время', ignore_case=True))
dp.register_message_handler(input_time, state=TimeFSM.time_needed)
dp.register_message_handler(contact_dev, Text(startswith='DEV', ignore_case=True))
dp.register_message_handler(show_apod, Text(contains='картинк', ignore_case=True))
dp.register_message_handler(catch_location, content_types=['location'])
dp.register_message_handler(admin, IDFilter(user_id=[DEV_TG_ID]))


executor.start_polling(dp, skip_updates=True)  # skip updates = сообщения, посланные боту пока тот онлайн будут проигнорированы
