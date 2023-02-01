from aiogram import executor, types, exceptions

from src.game import Durak
from bot import get_bot, on_startup

active_games = dict()
connected_players = list()
dp = get_bot()


@dp.message_handler(commands=['start', 'help'], state='*')
async def send_welcome(message: types.Message):
    await message.reply("🤌 Бот працює тільки в груповому чаті.")


@dp.message_handler(commands=['creategame'], state='*', chat_type=types.ChatType.GROUP)
async def start_game(message: types.Message):
    active_games.setdefault(message.chat.id, Durak(message.chat.id, dp))
    await message.reply(f"🃏 Набір гравців запущений!\n"
                         "🔹 Приєднатись - /connect\n"
                         "🔹 Запустити - /startgame")


@dp.message_handler(commands=['connect'], state='*', chat_type=types.ChatType.GROUP)
async def join_game(message: types.Message):
    if message.from_user.id in connected_players:
        return await message.reply("Ви вже і так підключені 🫤")
    game: Durak = active_games.get(message.chat.id)
    if game is None:
        return await message.reply("Ви ще не створили, а вже приєднуєтесь 🫤")
    if game.is_started:
        return await message.reply("Вибачай, але гра вже розпочата 🫡")
    if len(game.players) == 6:
        return await message.reply("Вибачай, але вже є 6 гравців. Це максимум 🫡")
    
    try:
        await dp.bot.send_message(chat_id=message.from_id, text="Успішно підключили тебе 😌")
    except exceptions.CantInitiateConversation:
        return await message.reply(text="Спочатку розпочни діалог з ботом в приватних повідомленнях 🫠")

    game.join(message.from_id, message.from_user.first_name)
    connected_players.append(message.from_user.id)
    return await message.reply(f"Підключили вас до гри 😌")


@dp.message_handler(commands=['leave'], state='*', chat_type=types.ChatType.GROUP)
async def leave_game(message: types.Message):
    game: Durak = active_games.get(message.chat.id)
    if game is None:
        return await message.reply("В цьому чаті гра не створена 🫤")
    
    game.leave(message.from_id)
    connected_players.remove(message.from_id)
    return await message.reply(f"Ви покинули гру 😥")


@dp.message_handler(commands=['players'], state='*', chat_type=types.ChatType.GROUP)
async def get_game_players(message: types.Message):
    game: Durak = active_games.get(message.chat.id)
    if game is None:
        return await message.reply("В цьому чаті гра не створена 🫤")
    players = [player.name for player in game.players]
    if not players:
        return await message.reply("Жодного підключеного гравця 😥")
    return await message.reply(f"📙 Підключені гравці: {str(players)}")


@dp.message_handler(commands=['startgame'], state='*', chat_type=types.ChatType.GROUP)
async def start_game(message: types.Message):
    game: Durak = active_games.get(message.chat.id)
    if game is None:
        return await message.reply("Ви ще не сторили гру, а вже починаєте 🤯")
    await game.start()


if __name__ == '__main__':
    dp = get_bot()
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
