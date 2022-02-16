from aiogram import Bot
from aiogram.dispatcher import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage


from config import TG_KEY

storage = MemoryStorage()
bot = Bot(token=TG_KEY)
dp = Dispatcher(bot, storage=storage)