import asyncio
import os
import random
import requests
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from dotenv import load_dotenv
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from sentence_transformers import SentenceTransformer
from gemini_ai import ask_gemini
from datetime import datetime

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Модель для поиска по описанию
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

hello_patrick = "CAACAgIAAxkBAAEcBfhpszLSSWz-Mfyw6CSmr18f8D_nogAC5AADlp-MDscIDPUzftb3OgQ"
blabla_patrick = "CAACAgIAAxkBAAEcLW1puJNFpk4pbVDS-7s3bx0zoupWQwACzgADlp-MDqZHXSdMxffEOgQ"

# ------------------- Работа с TMDB -------------------

def get_random_movie():
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        page = random.randint(1, 20)
        url = (
            f"https://api.themoviedb.org/3/discover/movie?api_key={TMDB_API_KEY}"
            f"&page={page}&language=ru-RU&sort_by=popularity.desc"
            f"&primary_release_date.lte={today}&vote_count.gte=200"
        )
        response = requests.get(url, timeout=10).json()
        results = response.get("results", [])
        if not results:
            raise Exception("Нет фильмов")
        movie = random.choice(results)
        return get_movie_by_id(movie["id"])
    except Exception as e:
        print("TMDB ERROR:", e)
        return {
            "title": "Ошибка подключения",
            "overview": "Не удалось получить фильм 😔",
            "poster_path": None
        }

def get_trending_movies():
    try:
        url = f"https://api.themoviedb.org/3/trending/movie/day?api_key={TMDB_API_KEY}&language=ru-RU"
        response = requests.get(url, timeout=10).json()
        movies = response.get("results", [])[:5]
        trending = [{"id": m["id"], "title": m.get("title", "Без названия"), 
                     "year": m.get("release_date", "??")[:4] if m.get("release_date") else "?"} for m in movies]
        return trending
    except Exception as e:
        print("TMDB TRENDING ERROR:", e)
        return []

def get_movie_by_id(movie_id):
    try:
        details = requests.get(f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=ru-RU").json()
        credits = requests.get(f"https://api.themoviedb.org/3/movie/{movie_id}/credits?api_key={TMDB_API_KEY}&language=ru-RU").json()
        videos = requests.get(f"https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={TMDB_API_KEY}&language=ru-RU").json()

        director = next((c["name"] for c in credits.get("crew", []) if c.get("job") == "Director"), "—")
        actors = ", ".join([a["name"] for a in credits.get("cast", [])[:3]])
        trailer = next((f"https://youtube.com/watch?v={v['key']}" for v in videos.get("results", []) 
                        if v.get("type") == "Trailer" and v.get("site") == "YouTube"), None)
        genres = ", ".join([g["name"] for g in details.get("genres", [])])

        return {
            "id": movie_id,
            "title": details.get("title", "Без названия"),
            "year": details.get("release_date", "??")[:4] if details.get("release_date") else "?",
            "rating": details.get("vote_average", "??"),
            "runtime": details.get("runtime", "??"),
            "genres": genres if genres else [],
            "overview": details.get("overview", "Описание отсутствует."),
            "tagline": details.get("tagline", "~~~~~~~~~~~~~~~"),
            "director": director,
            "actors": actors,
            "poster_path": details.get("poster_path"),
            "trailer": trailer
        }
    except Exception as e:
        print("TMDB ERROR:", e)
        return None

# ------------------- Клавиатура -------------------

def get_user_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚀 Старт")],
            [KeyboardButton(text="🎲 Случайный фильм"), KeyboardButton(text="🗓 В тренде")],
            [KeyboardButton(text="🔍 Умный поиск"), KeyboardButton(text="🔑 По описанию")],
            [KeyboardButton(text="📜 Все команды")]
        ],
        resize_keyboard=True
    )

# ------------------- Отправка фильма -------------------

async def send_movie(chat_id, movie):
    poster_path = movie.get("poster_path")
    poster = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
    runtime_text = f"{movie['runtime'] // 60}ч {movie['runtime'] % 60}м" if isinstance(movie.get('runtime'), int) else "—"
    actors = movie.get('actors', 'Неизвестно')

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
    buttons.append([InlineKeyboardButton(text="🤖 Спросить ИИ", callback_data=f"ask_ai_{movie['id']}")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    if poster:
        await bot.send_photo(chat_id, poster, caption=text, parse_mode="HTML", reply_markup=keyboard)
    else:
        await bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=keyboard)

async def send_random_movie(chat_id):
    movie = await asyncio.to_thread(get_random_movie)
    print(f"[INFO] Найден фильм: {movie.get('title', 'без названия')}")
    await send_movie(chat_id, movie)

async def send_trending_movies(chat_id):
    trending = get_trending_movies()
    if not trending:
        await bot.send_message(chat_id, "Не удалось получить трендовые фильмы 😔")
        return
    buttons = [[InlineKeyboardButton(text=f"{m['title']} ({m['year']})", callback_data=f"trending_{m['id']}")] for m in trending]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await bot.send_message(chat_id, "🔥 Трендовые фильмы сегодня:", reply_markup=keyboard)

# ------------------- Обработка ИИ -------------------

@dp.callback_query(F.data.startswith("ask_ai_"))
async def ask_ai_callback(callback: types.CallbackQuery):
    await callback.answer()
    movie_id = int(callback.data.split("_")[2])
    movie = get_movie_by_id(movie_id)
    movie_title = movie.get("title", "фильм") if movie else "фильм"

    chat_id = callback.message.chat.id
    print(f"[INFO] Пользователь {callback.from_user.id} спрашивает ИИ про {movie_title}")
    loading_msg = await bot.send_message(chat_id, f"🤖 ИИ думает про <b>{movie_title}</b>...", parse_mode="HTML")

    async def handle_ai_question(msg: types.Message):
        if msg.chat.id != chat_id:
            return
        print(f"[INFO] Получен вопрос: {msg.text}")
        try:
            answer = await ask_gemini(msg.text)
            print(f"[INFO] Ответ ИИ: {answer[:50]}...")
            await msg.answer(f"🤖 Ответ ИИ:\n{answer}")
        except Exception as e:
            print(f"[ERROR] Ошибка при запросе ИИ: {e}")
            await msg.answer("⚠️ Произошла ошибка при обращении к ИИ")
        finally:
            dp.message_handlers.unregister(handle_ai_question)
            try:
                await loading_msg.delete()
            except:
                pass

    dp.message_handlers.register(handle_ai_question)

# ------------------- Команды -------------------

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    try:
        await message.answer_sticker(sticker=hello_patrick)
    except:
        pass
    caption = (
        "<b>🎬 Добро пожаловать в мир кино!</b>\n\n"
        "Я — твой персональный гид по фильмам. Помогу найти что посмотреть сегодня 🍿\n\n"
        "<b>Что я умею:</b>\n"
        "🎲 Случайный фильм — /random\n"
        "🗓 В тренде — /trending\n"
        "🔍 Умный поиск — /search\n"
        "🔑 По описанию — /description\n\n"
        "Можно использовать кнопки или команды.\n\n"
        "──────────────────\n"
        "🆘 Вопросы крутым разработчикам:\n"
        "👨‍💻 @regsaff | 👨‍💻 @lyuuubaaa"
    )
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

@dp.message(F.text == "🚀 Старт")
async def start_button(message: types.Message):
    await start_cmd(message)

@dp.message(F.text == "🎲 Случайный фильм")
async def random_button(message: types.Message):
    print(f"[INFO] Пользователь {message.from_user.id} нажал '🎲 Случайный фильм'")
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
        "──────────────────\n"
        "🆘 Вопросы крутым разработчикам:\n"
        "👨‍💻 @regsaff | 👨‍💻 @lyuuubaaa"
    )
    await message.answer(commands, parse_mode="HTML")

@dp.message()
async def unknown(message: types.Message):
    try:
        await message.answer_sticker(sticker=blabla_patrick)
    except:
        pass
    await message.answer(
        "Ух ты, заумно как... Давай лучше на «🚀 Старт» нажмём?👇",
        reply_markup=get_user_keyboard()
    )

# ------------------- Callback -------------------

@dp.callback_query(F.data == "random_movie")
async def random_movie_callback(callback: types.CallbackQuery):
    await callback.answer()
    chat_id = callback.message.chat.id
    print(f"[INFO] Пользователь {callback.from_user.id} нажал 'Другой фильм'")
    try:
        await callback.message.edit_reply_markup(None)
    except: pass

    loading_msg = await bot.send_message(chat_id, "🎬 Ищу фильм...")
    try:
        movie = await asyncio.to_thread(get_random_movie)
        print(f"[INFO] Найден фильм: {movie.get('title', 'без названия')}")
        await asyncio.sleep(0.2)
        await send_movie(chat_id, movie)
    except Exception as e:
        print(f"[ERROR] RANDOM ERROR: {e}")
        await bot.send_message(chat_id, "Ошибка 😔 Попробуй ещё раз")
    finally:
        try: await bot.delete_message(chat_id, callback.message.message_id)
        except: pass
        try: await loading_msg.delete()
        except: pass

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
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())