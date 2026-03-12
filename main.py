import asyncio
import os
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    sticker_id = "CAACAgIAAxkBAAEcBfhpszLSSWz-Mfyw6CSmr18f8D_nogAC5AADlp-MDscIDPUzftb3OgQ"
    
    caption = (
        "<b>🎬 Добро пожаловать в мир кино!</b>\n\n"
        "Я — твой персональный гид по кинематографу. Помогу найти "
        "идеальный фильм под любое настроение. ✨\n\n"
        "<b>Что я умею:</b>\n"
        "🍿 <i>Случайный подбор</i> — если лень выбирать\n"
        "🌟 <i>Фильм дня</i> — то, что нельзя пропустить\n"
        "🔍 <i>Умный поиск</i> — по жанрам и годам\n"
        "🔑 <i>По описанию</i> — подберу фильм по ключевым словам\n\n"
        "────────────────────\n"
        "🆘 <b>Нужна помощь?</b> Пиши крутым создателям:\n"
        "👨‍💻 @regsaff | 👨‍💻 @lyuuubaaa"
    )

    # builder = InlineKeyboardBuilder()
    # builder.row(types.InlineKeyboardButton(text="🎲 Случайный фильм", callback_data="random_film"))
    # builder.row(
    #     types.InlineKeyboardButton(text="🗓 Фильм дня", callback_data="day_film"),
    #     types.InlineKeyboardButton(text="⚙️ Параметры", callback_data="params_film")
    # )
    # builder.row(types.InlineKeyboardButton(text="🔑 По описанию", callback_data="description_film"))

    try:
        await message.answer_sticker(sticker=sticker_id)
    except Exception:
        pass 
        
    await message.answer(
        text=caption, 
        parse_mode="HTML", 
        reply_markup=builder.as_markup()
    )

@dp.message(Command("help"))
async def help_command(message: types.Message):
    await start(message)

@dp.message(F.text)
async def echo(message: types.Message):
    await message.answer(
        f"Ты написал: <i>{message.text}</i>.\n\n"
        "Чтобы выбрать фильм, используй кнопки в меню или нажми /start!", 
        parse_mode="HTML"
    )

async def main():
    print("Бот успешно запущен и готов к работе! 🚀")
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен.")