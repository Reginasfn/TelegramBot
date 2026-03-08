import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from dotenv import load_dotenv
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()


# Клавиатура снизу
def get_user_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="▶️ start")],
            [
                KeyboardButton(text="🎲 Случайный фильм"),
                KeyboardButton(text="🗓 Фильм дня")
            ],
            [
                KeyboardButton(text="🔍 Умный поиск"),
                KeyboardButton(text="🔑 По описанию")
            ],
            [KeyboardButton(text="📜 Все команды")]
        ],
        resize_keyboard=True
    )


# Команда START
@dp.message(Command("start"))
async def start(message: types.Message):

    sticker_id = "CAACAgIAAxkBAAEcBfhpszLSSWz-Mfyw6CSmr18f8D_nogAC5AADlp-MDscIDPUzftb3OgQ"

    caption = (
        "<b>🎬 Добро пожаловать в мир кино!</b>\n\n"
        "Я — твой персональный гид по фильмам. Помогу найти "
        "что посмотреть сегодня 🍿\n\n"

        "<b>Что я умею:</b>\n"
        "🎲 Случайный фильм — /random\n"
        "🗓 Фильм дня — /day\n"
        "🔍 Умный поиск — /search\n"
        "🔑 По описанию — /description\n\n"

        "Можно использовать кнопки или команды.\n\n"

        "─────────────────\n"
        "🆘 Вопросы крутым разработчикам:\n"
        "👨‍💻 @regsaff | 👨‍💻 @lyuuubaaa"
    )

    try:
        await message.answer_sticker(sticker=sticker_id)
    except Exception:
        pass

    await message.answer(
        caption,
        parse_mode="HTML",
        reply_markup=get_user_keyboard()
    )


# Команды
@dp.message(Command("random"))
async def random_movie(message: types.Message):
    await message.answer("🎲 Подбираю случайный фильм...")


@dp.message(Command("day"))
async def day_movie(message: types.Message):
    await message.answer("🗓 Вот фильм дня!")


@dp.message(Command("search"))
async def smart_search(message: types.Message):
    await message.answer("🔍 Умный поиск пока в разработке")


@dp.message(Command("description"))
async def description_movie(message: types.Message):
    await message.answer("Напиши описание фильма, который ищешь")


# Обработка кнопок
@dp.message(F.text == "▶️ start")
async def start_button(message: types.Message):
    await start(message)


@dp.message(F.text == "🎲 Случайный фильм")
async def random_button(message: types.Message):
    await random_movie(message)


@dp.message(F.text == "🗓 Фильм дня")
async def day_button(message: types.Message):
    await day_movie(message)


@dp.message(F.text == "🔍 Умный поиск")
async def search_button(message: types.Message):
    await smart_search(message)


@dp.message(F.text == "🔑 По описанию")
async def description_button(message: types.Message):
    await description_movie(message)


@dp.message(F.text == "📜 Все команды")
async def show_commands(message: types.Message):

    commands = (
        "<b>📜 Все команды:</b>\n\n"
        "/start — запустить бота\n"
        "/random — случайный фильм\n"
        "/day — фильм дня\n"
        "/search — умный поиск\n"
        "/description — поиск по описанию\n\n"

        "─────────────────\n"
        "🆘 Вопросы крутым разработчикам:\n"
        "👨‍💻 @regsaff | 👨‍💻 @lyuuubaaa"
    )

    await message.answer(commands, parse_mode="HTML")


# Если пользователь пишет что-то другое
@dp.message()
async def unknown(message: types.Message):

    await message.answer(
        "Чтобы начать работу нажми кнопку ▶️ start 👇",
        reply_markup=get_user_keyboard()
    )


# Запуск бота
async def main():

    print("Бот успешно запущен 🚀")

    await bot.set_my_commands([
        types.BotCommand(command="start", description="Запустить бота"),
        types.BotCommand(command="random", description="Случайный фильм"),
        types.BotCommand(command="day", description="Фильм дня"),
        types.BotCommand(command="search", description="Умный поиск"),
        types.BotCommand(command="description", description="Поиск по описанию")
    ])

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())