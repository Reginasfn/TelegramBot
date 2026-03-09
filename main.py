import asyncio
import os
import random
import requests
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from dotenv import load_dotenv
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from sentence_transformers import SentenceTransformer, util

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Модель для поиска по описанию
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

hello_patrick = "CAACAgIAAxkBAAEcBfhpszLSSWz-Mfyw6CSmr18f8D_nogAC5AADlp-MDscIDPUzftb3OgQ"

# ------------------- Работа с TMDB -------------------

def get_random_movie():
    try:
        page = random.randint(1, 10)
        url = f"https://api.themoviedb.org/3/discover/movie?api_key={TMDB_API_KEY}&page={page}&language=ru-RU"
        response = requests.get(url, timeout=10).json()

        movie = random.choice(response["results"])
        movie_id = movie["id"]

        # детали
        details_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=ru-RU"
        details = requests.get(details_url).json()

        # кредиты
        credits_url = f"https://api.themoviedb.org/3/movie/{movie_id}/credits?api_key={TMDB_API_KEY}&language=ru-RU"
        credits = requests.get(credits_url).json()

        # трейлер
        video_url = f"https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={TMDB_API_KEY}&language=ru-RU"
        videos = requests.get(video_url).json()

        director = "—"
        for crew in credits.get("crew", []):
            if crew.get("job") == "Director":
                director = crew.get("name")
                break

        actors = ", ".join([a["name"] for a in credits.get("cast", [])[:3]])

        trailer = None
        for v in videos.get("results", []):
            if v.get("type") == "Trailer" and v.get("site") == "YouTube":
                trailer = f"https://youtube.com/watch?v={v['key']}"
                break

        genres = ", ".join([g["name"] for g in details.get("genres", [])])

        return {
            "title": details.get("title", "Без названия"),
            "year": details.get("release_date", "??")[:4] if details.get("release_date") else "?",
            "rating": details.get("vote_average", "??"),
            "runtime": details.get("runtime", "??"),
            "genres": genres if genres else [],
            "overview": details.get("overview", "Описание отсутствует. Но фильм все равно потрясающий."),
            "tagline": details.get("tagline", "~~~~~~~~~~~~~~~"),
            "director": director if director else "Неизвестный",
            "actors": actors if actors else [],
            "poster_path": details.get("poster_path"),
            "trailer": trailer if trailer else None
        }

    except Exception as e:
        print("TMDB ERROR:", e)
        return {
            "title": "Ошибка подключения",
            "overview": "Не удалось получить фильм. Попробуй позже."
        }

def get_trending_movies():
    try:
        url = f"https://api.themoviedb.org/3/trending/movie/day?api_key={TMDB_API_KEY}&language=ru-RU"
        response = requests.get(url, timeout=10).json()
        movies = response.get("results", [])[:5]
        trending = []
        for m in movies:
            trending.append({
                "id": m["id"],
                "title": m.get("title", "Без названия"),
                "year": m.get("release_date", "??")[:4] if m.get("release_date") else "?",
            })
        return trending
    except Exception as e:
        print("TMDB TRENDING ERROR:", e)
        return []

def get_movie_by_id(movie_id):
    try:
        details_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=ru-RU"
        details = requests.get(details_url).json()

        credits_url = f"https://api.themoviedb.org/3/movie/{movie_id}/credits?api_key={TMDB_API_KEY}&language=ru-RU"
        credits = requests.get(credits_url).json()

        video_url = f"https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={TMDB_API_KEY}&language=ru-RU"
        videos = requests.get(video_url).json()

        director = "—"
        for crew in credits.get("crew", []):
            if crew.get("job") == "Director":
                director = crew.get("name")
                break

        actors = ", ".join([a["name"] for a in credits.get("cast", [])[:3]])

        trailer = None
        for v in videos.get("results", []):
            if v.get("type") == "Trailer" and v.get("site") == "YouTube":
                trailer = f"https://youtube.com/watch?v={v['key']}"
                break

        genres = ", ".join([g["name"] for g in details.get("genres", [])])

        return {
            "title": details.get("title", "Без названия"),
            "year": details.get("release_date", "??")[:4] if details.get("release_date") else "?",
            "rating": details.get("vote_average", "??"),
            "runtime": details.get("runtime", "??"),
            "genres": genres if genres else [],
            "overview": details.get("overview", "Описание отсутствует."),
            "tagline": details.get("tagline", "~~~~~~~~~~~~~~~"),
            "director": director if director else "Неизвестный",
            "actors": actors if actors else [],
            "poster_path": details.get("poster_path"),
            "trailer": trailer if trailer else None
        }
    except Exception as e:
        print("TMDB ERROR:", e)
        return None

# ------------------- Отправка фильма -------------------

async def send_movie(chat_id, movie):
    poster_path = movie.get("poster_path")
    if poster_path:
        poster = f"https://image.tmdb.org/t/p/w500{poster_path}"
    else:
        poster = None

    runtime = movie.get("runtime", 0)
    if isinstance(runtime, int) and runtime > 0:
        hours = runtime // 60
        minutes = runtime % 60
        runtime_text = f"{hours}ч {minutes}м"
    else:
        runtime_text = "—"

    actors = movie.get("actors", "")
    if actors:
        actors_list = actors.split(",")[:3]
        actors = ", ".join(actors_list)
    else:
        actors = "Неизвестно"

    text = f"""
🎬 <b>{movie.get('title','Без названия')} ({movie.get('year','?')})</b>

<i>{movie.get('tagline','')}</i>

⭐️ <b>{movie.get('rating','—')}</b> | 🎭 <b>{movie.get('genres','—')}</b> | 🕒 <b>{runtime_text}</b>

🎬 <b>Режиссёр:</b> {movie.get('director','—')}
👥 <b>Актёры:</b> {actors}

📝 <b>Описание</b>
<tg-spoiler>{movie.get('overview','Нет описания')}</tg-spoiler>
"""

    buttons = []
    if movie.get("trailer"):
        buttons.append([InlineKeyboardButton(text="▶️ Трейлер", url=movie["trailer"])])
    buttons.append([InlineKeyboardButton(text="🎲 Другой фильм", callback_data="random_movie")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    if poster:
        await bot.send_photo(chat_id, poster, caption=text, parse_mode="HTML", reply_markup=keyboard)
    else:
        await bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=keyboard)

async def send_random_movie(chat_id):
    movie = get_random_movie()
    await send_movie(chat_id, movie)

async def send_trending_movies(chat_id):
    trending = get_trending_movies()
    if not trending:
        await bot.send_message(chat_id, "Не удалось получить трендовые фильмы 😔")
        return
    buttons = [
        [InlineKeyboardButton(text=f"{m['title']} ({m['year']})", callback_data=f"trending_{m['id']}")]
        for m in trending
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await bot.send_message(chat_id, "🔥 Трендовые фильмы сегодня:", reply_markup=keyboard)

# ------------------- Клавиатура -------------------

def get_user_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="▶️ start")],
            [KeyboardButton(text="🎲 Случайный фильм"), KeyboardButton(text="🗓 В тренде")],
            [KeyboardButton(text="🔍 Умный поиск"), KeyboardButton(text="🔑 По описанию")],
            [KeyboardButton(text="📜 Все команды")]
        ],
        resize_keyboard=True
    )

# ------------------- Команды -------------------

@dp.message(Command("start"))
async def start(message: types.Message):
    sticker_id = hello_patrick
    caption = (
        "<b>🎬 Добро пожаловать в мир кино!</b>\n\n"
        "Я — твой персональный гид по фильмам. Помогу найти "
        "что посмотреть сегодня 🍿\n\n"
        "<b>Что я умею:</b>\n"
        "🎲 Случайный фильм — /random\n"
        "🗓 В тренде — /trending\n"
        "🔍 Умный поиск — /search\n"
        "🔑 По описанию — /description\n\n"
        "Можно использовать кнопки или команды.\n\n"
        "─────────────────────────\n"
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

@dp.message(Command("trending"))
async def trending_cmd(message: types.Message):
    await send_trending_movies(message.chat.id)

@dp.message(Command("search"))
async def smart_search_cmd(message: types.Message):
    await message.answer("🔍 Умный поиск пока в разработке")

@dp.message(Command("description"))
async def description_movie_cmd(message: types.Message):
    await message.answer("🔑 По описанию пока в разработке")

# ------------------- Кнопки -------------------

@dp.message(F.text == "▶️ start")
async def start_button(message: types.Message):
    await start(message)

@dp.message(F.text == "🎲 Случайный фильм")
async def random_button(message: types.Message):
    await send_random_movie(message.chat.id)

@dp.message(F.text == "🗓 В тренде")
async def trending_button(message: types.Message):
    await send_trending_movies(message.chat.id)

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
        "/trending — фильмы в тренде\n"
        "/search — умный поиск\n"
        "/description — поиск по описанию\n\n"
        "──────────────────────────────────\n"
        "🆘 Вопросы крутым разработчикам:\n"
        "👨‍💻 @regsaff | 👨‍💻 @lyuuubaaa"
    )
    await message.answer(commands, parse_mode="HTML")

@dp.message()
async def unknown(message: types.Message):
    await message.answer("Чтобы начать работу нажми кнопку ▶️ start 👇", reply_markup=get_user_keyboard())

# ------------------- Callback -------------------

@dp.callback_query(F.data == "random_movie")
async def random_movie_callback(callback: types.CallbackQuery):
    await callback.answer()
    movie = get_random_movie()
    try: await callback.message.delete()
    except: pass
    await send_movie(callback.message.chat.id, movie)

@dp.callback_query(F.data.startswith("trending_"))
async def trending_movie_callback(callback: types.CallbackQuery):
    await callback.answer()
    movie_id = int(callback.data.split("_")[1])
    movie = get_movie_by_id(movie_id)
    if not movie:
        await bot.send_message(callback.message.chat.id, "Ошибка при получении фильма 😔")
        return
    try: await callback.message.delete()
    except: pass
    await send_movie(callback.message.chat.id, movie)

# ------------------- Запуск -------------------

async def main():
    print("Бот успешно запущен 🚀")
    await bot.set_my_commands([
        types.BotCommand(command="start", description="Запустить бота"),
        types.BotCommand(command="random", description="Случайный фильм"),
        types.BotCommand(command="trending", description="Фильмы в тренде"),
        types.BotCommand(command="search", description="Умный поиск"),
        types.BotCommand(command="description", description="Поиск по описанию")
    ])
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())