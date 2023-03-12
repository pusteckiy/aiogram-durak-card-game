from decouple import config
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage


TOKEN = config('TOKEN')


def get_bot():
    storage = MemoryStorage()
    bot = Bot(token=TOKEN)
    dp = Dispatcher(bot, storage=storage)
    return dp


async def set_default_commands(dp):
    await dp.bot.set_my_commands([
        types.BotCommand("creategame", "Створити"),
        types.BotCommand("connect", "Підключитись"),
        types.BotCommand("leave", "Покинути"),
        types.BotCommand("startgame", "Запустити"),
        types.BotCommand("players", "Підключені гравці"),
    ])


async def on_startup(dp):
    await set_default_commands(dp)
