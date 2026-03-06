import asyncio
import os
import random
import requests
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
POISKKINO_API_KEY = "MGN4NW1-N0YMZKG-MYAARG4-XWWW1GG"

bot = Bot(token=TOKEN)
dp = Dispatcher()
POISKKINO_BASE = "https://api.poiskkino.dev/v1.4"


def poiskkino_request(endpoint: str, params: dict | None = None) -> dict | None:
    headers = {
        "accept": "application/json",
        "X-API-KEY": POISKKINO_API_KEY
    }
    
    url = f"{POISKKINO_BASE}{endpoint}"
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return data.get("docs", data) if "docs" in data else data
    except Exception as e:
        print("PoiskKino error:", e)
        return None


def get_random_movie() -> dict | None:
    """Берём популярные фильмы и возвращаем лучший"""
    # Получаем список фильмов (limit=50 для разнообразия)
    data = poiskkino_request("/movie", {"limit": 50})
    
    if not data:
        print("Нет данных от /movie")
        return None
    
    movies = data if isinstance(data, list) else []
    if not movies:
        print("Пустой список фильмов")
        return None
    
    # Фильтруем только хорошие фильмы (есть название и рейтинг IMDb > 5)
    good_movies = []
    for movie in movies:
        title = movie.get("name") or movie.get("alternativeName") or movie.get("enName")
        if title:
            imdb_rating = get_rating(movie, "imdb")
            if imdb_rating and imdb_rating > 5:
                good_movies.append(movie)
    
    if not good_movies:
        # Берём любой с названием
        for movie in movies:
            if movie.get("name") or movie.get("alternativeName"):
                good_movies.append(movie)
                break
    
    movie = random.choice(good_movies)
    
    # Полная инфа по ID
    if movie.get("id"):
        full_movie = poiskkino_request(f"/movie/{movie['id']}")
        if full_movie:
            movie = full_movie
    
    return movie


def get_rating(movie: dict, source: str = "imdb") -> float:
    """Извлекает рейтинг из сложной структуры"""
    try:
        ratings = movie.get("rating", {})
        if isinstance(ratings, dict):
            rating_key = ratings.get(source)
            if isinstance(rating_key, dict):
                return float(rating_key.get("value", 0))
            return float(rating_key or 0)
        return float(ratings.get(source, {}).get("value", 0) if isinstance(ratings, dict) else 0)
    except:
        return 0


def format_movie(movie: dict) -> str:
    """Красивое форматирование с правильным парсингом"""
    # Название (приоритет: ru → en → alternative)
    title = movie.get("name") or movie.get("enName") or movie.get("alternativeName") or "Без названия"
    year = movie.get("year") or "-"
    
    # Рейтинги
    kp_rating = get_rating(movie, "kp")
    imdb_rating = get_rating(movie, "imdb")
    
    # Жанры
    genres_raw = movie.get("genres", [])
    genres = []
    if isinstance(genres_raw, list):
        for g in genres_raw[:3]:
            genres.append(g.get("name") or g if isinstance(g, str) else str(g))
    genres_text = ", ".join(genres) if genres else ""
    
    # Описание
    plot = movie.get("description") or movie.get("shortDescription") or "Описание отсутствует."
    plot = plot[:250] + "..." if len(plot) > 250 else plot
    
    # Собираем
    parts = [f"<b>{title}</b>"]
    if year != "-":
        parts.append(f" ({year})")
    
    if imdb_rating:
        parts.append(f"\n🌍 <b>IMDb: {imdb_rating:.1f}</b>")
    if kp_rating:
        parts.append(f"\n⭐ <b>КП: {kp_rating:.1f}</b>")
    
    if genres_text:
        parts.append(f"\n🎭 <b>{genres_text}</b>")
    
    parts.append(f"\n\n{plot}")
    
    return "".join(parts)


@dp.message(Command("start"))
async def start(message: types.Message):
    sticker_id = "CAACAgIAAxkBAAEcBfhpszLSSWz-Mfyw6CSmr18f8D_nogAC5AADlp-MDscIDPUzftb3OgQ"
    
    caption = (
        "🎬 <b>ФИЛЬМ БОТ v2.0</b>\n\n"
        "🤖 Твой кинокурьер с ПоискКино API\n\n"
        "🎲 <b>Случайный хит</b> из топовых фильмов\n\n"
        "👨‍💻 @regsaff | @lyuuubaaa"
    )

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🎲 Случайный фильм", callback_data="random_film"))

    try:
        await message.answer_sticker(sticker=sticker_id)
    except:
        pass 
        
    await message.answer(
        text=caption, 
        parse_mode="HTML", 
        reply_markup=builder.as_markup()
    )


@dp.callback_query(F.data == "random_film")
async def random_film_handler(callback: types.CallbackQuery):
    await callback.answer("🎬 Подбираю шедевр...")
    
    movie = get_random_movie()
    if not movie:
        await callback.message.answer("😔 Не нашёл годных фильмов. Жми ещё раз!")
        return

    text = format_movie(movie)
    
    # Постер
    poster = (movie.get("poster", {}).get("url") or 
              movie.get("posterUrl") or 
              movie.get("imageUrl") or 
              None)
    
    if poster:
        try:
            await callback.message.answer_photo(photo=poster, caption=text, parse_mode="HTML")
        except:
            await callback.message.answer(text, parse_mode="HTML")
    else:
        await callback.message.answer(text, parse_mode="HTML")


@dp.message(F.text)
async def echo(message: types.Message):
    await message.answer("🎬 /start — для случайного фильма!")


async def main():
    print("🎬 ПоискКино Bot v2.0 запущен! 🚀")
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
