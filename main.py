import asyncio
import os
from aiogram import Bot, Dispatcher, types, F 
from aiogram.filters import Command
from dotenv import load_dotenv

load_dotenv()

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer('Привет! Я эхо-бот. Напиши мне что-нибудь! 🎉')

@dp.message(F.text)
async def echo(message: types.Message):
    await message.answer(message.text)

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())