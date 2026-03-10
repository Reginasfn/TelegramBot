import os
import openai  # если используем OpenAI/Gemini
from dotenv import load_dotenv

load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_KEY")

openai.api_key = GEMINI_KEY

async def ask_gemini(question: str) -> str:
    """
    Отправляет вопрос пользователю в Gemini AI и возвращает ответ.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gemini-1.5",
            messages=[{"role": "user", "content": question}],
            temperature=0.7,
            max_tokens=500
        )
        answer = response.choices[0].message.content
        return answer
    except Exception as e:
        print("Gemini ERROR:", e)
        return "🤖 Извини, ИИ сейчас недоступен. Попробуй позже."