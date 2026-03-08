import asyncio
import os
import random
import requests
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from dotenv import load_dotenv
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from sentence_transformers import SentenceTransformer, util

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Модель для поиска по описанию
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')


# Работа с TMDB
def get_random_movie():
    try:
        page = random.randint(1, 10)
        url = f"https://api.themoviedb.org/3/discover/movie?api_key={TMDB_API_KEY}&page={page}&language=ru-RU"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        results = response.json().get("results", [])
        if not results:
            raise Exception("Фильмы не найдены")
        movie = random.choice(results)
        return {
            "title": movie.get("title", "Без названия"),
            "rating": movie.get("vote_average", "?"),
            "overview": movie.get("overview", "Описание отсутствует"),
            "year": movie.get("release_date", "?")[:4] if movie.get("release_date") else "?",
            "poster_path": movie.get("poster_path")
        }
    except Exception as e:
        print("TMDB ERROR:", e)
        return {
            "title": "Ошибка подключения",
            "rating": "-",
            "overview": "Не удалось получить фильм. Попробуй позже.",
            "year": "-",
            "poster_path": None
        }


# Отправка фильма
async def send_movie(chat_id, movie):
    text = f"""
🎬 <b>{movie['title']}</b>
⭐ Рейтинг: {movie.get('rating', '-') }
📅 Год: {movie.get('year', '-') }

📝 {movie.get('overview', '-') }
"""
    try:
        if movie.get("poster_path"):
            poster_url = "https://image.tmdb.org/t/p/w500" + movie["poster_path"]
            await bot.send_photo(chat_id, poster_url, caption=text, parse_mode="HTML")
        else:
            await bot.send_message(chat_id, text, parse_mode="HTML")
    except:
        await bot.send_message(chat_id, text, parse_mode="HTML")


async def send_random_movie(chat_id):
    movie = get_random_movie()
    await send_movie(chat_id, movie)


async def send_day_movie(chat_id):
    # пока тоже случайный
    movie = get_random_movie()
    await send_movie(chat_id, movie)


# Клавиатура снизу
def get_user_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="▶️ start")],
            [KeyboardButton(text="🎲 Случайный фильм"), KeyboardButton(text="🗓 Фильм дня")],
            [KeyboardButton(text="🔍 Умный поиск"), KeyboardButton(text="🔑 По описанию")],
            [KeyboardButton(text="📜 Все команды")]
        ],
        resize_keyboard=True
    )


# Команды
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
    await message.answer(caption, parse_mode="HTML", reply_markup=get_user_keyboard())


@dp.message(Command("random"))
async def random_movie_cmd(message: types.Message):
    await send_random_movie(message.chat.id)


@dp.message(Command("day"))
async def day_movie_cmd(message: types.Message):
    await send_day_movie(message.chat.id)


@dp.message(Command("search"))
async def smart_search_cmd(message: types.Message):
    await message.answer("🔍 Умный поиск пока в разработке")


@dp.message(Command("description"))
async def description_movie_cmd(message: types.Message):
    await message.answer("🔑 По описанию пока в разработке")


# Кнопки
@dp.message(F.text == "▶️ start")
async def start_button(message: types.Message):
    await start(message)


@dp.message(F.text == "🎲 Случайный фильм")
async def random_button(message: types.Message):
    await send_random_movie(message.chat.id)


@dp.message(F.text == "🗓 Фильм дня")
async def day_button(message: types.Message):
    await send_day_movie(message.chat.id)


@dp.message(F.text == "🔍 Умный поиск")
async def search_button(message: types.Message):
    await message.answer("🔍 Умный поиск пока в разработке")


@dp.message(F.text == "🔑 По описанию")
async def description_button(message: types.Message):
    await message.answer("🔑 По описанию пока в разработке")


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