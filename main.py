import logging
import os
import aiohttp
import asyncio
from aiohttp import web
from dotenv import load_dotenv

# ========================================
# ЭТАП 1: Загрузка переменных окружения
# ========================================
load_dotenv()

# ========================================
# ЭТАП 2: Настройка логирования
# ========================================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ========================================
# ЭТАП 3: Константы Chutes AI
# ========================================
CHUTES_API_URL = os.getenv("CHUTES_API_URL", "https://llm.chutes.ai/v1/chat/completions")
CHUTES_API_KEY = os.getenv("CHUTES_API_KEY", "")
MODEL_NAME = os.getenv("MODEL_NAME", "default")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
PORT = int(os.getenv("PORT", "8080"))

# ========================================
# ЭТАП 4: Хранилище истории диалога
# ========================================
chat_histories: dict[int, list[dict]] = {}


# ========================================
# ЭТАП 5: Функция обращения к Chutes AI
# ========================================
async def get_ai_response(user_message: str) -> str:
    """Отправляет сообщение в Chutes API и получает ответ."""
    messages = [
        {"role": "system", "content": "Ты полезный ассистент. Отвечай на русском языке кратко и по делу."},
        *chat_histories.get(0, []),
        {"role": "user", "content": user_message},
    ]

    headers = {
        "Authorization": f"Bearer {CHUTES_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "max_tokens": 500,
        "temperature": 0.7,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(CHUTES_API_URL, json=payload, headers=headers) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    logger.error(f"Chutes API error: {resp.status} - {error_text}")
                    return "😅 Произошла ошибка при обработке запроса. Попробуй позже."
                
                data = await resp.json()
                assistant_message = data["choices"][0]["message"]["content"]
                
                if 0 not in chat_histories:
                    chat_histories[0] = []
                chat_histories[0].append({"role": "user", "content": user_message})
                chat_histories[0].append({"role": "assistant", "content": assistant_message})
                
                return assistant_message

    except aiohttp.ClientError as e:
        logger.error(f"Network error: {e}")
        return "🌐 Ошибка сети. Проверь подключение."
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return "⚠️ Произошла непредвиденная ошибка."


# ========================================
# ЭТАП 6: Telegram Bot API (чистый aiohttp)
# ========================================
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"


async def tg_request(method: str, data: dict = None) -> dict:
    """Отправляет запрос к Telegram Bot API."""
    url = f"{TELEGRAM_API_URL}/{method}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as resp:
                if resp.status != 200:
                    logger.error(f"Telegram API error: {resp.status}")
                    return {}
                return await resp.json()
    except Exception as e:
        logger.error(f"Telegram request error: {e}")
        return {}


async def delete_webhook():
    """Сбрасывает webhook Telegram."""
    logger.info("Сброс webhook...")
    await tg_request("deleteWebhook")


async def send_message(chat_id: int, text: str) -> bool:
    """Отправляет сообщение пользователю."""
    result = await tg_request("sendMessage", {"chat_id": chat_id, "text": text})
    return bool(result.get("ok"))


async def get_updates(offset: int = None) -> list:
    """Получает обновления от Telegram."""
    data = {"timeout": 0}
    if offset is not None:
        data["offset"] = offset
    result = await tg_request("getUpdates", data)
    return result.get("result", [])


# ========================================
# ЭТАП 7: Обработка сообщений
# ========================================
async def handle_message(update: dict) -> None:
    """Обрабатывает одно сообщение."""
    message = update.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")
    message_id = message.get("message_id")

    if not text:
        return

    # Команда /start
    if text == "/start":
        await send_message(chat_id, 
            f"Привет! 👋\n\n"
            f"Я чат-бот с AI от Chutes. "
            f"Напиши мне что-нибудь, и я отвечу! 🤖")
        return

    # Команда /help
    if text == "/help":
        await send_message(chat_id,
            "📖 Справка:\n\n"
            "• Просто пиши сообщения — я отвечу с помощью AI\n"
            "• /start — начать общение\n"
            "• /help — показать эту справку")
        return

    # Обычный текст — AI-ответ
    await send_message(chat_id, "🤖 Думаю...")
    ai_response = await get_ai_response(text)
    await send_message(chat_id, ai_response)


# ========================================
# ЭТАП 9: HTTP-сервер + polling
# ========================================
async def health_check(request):
    """Проверка, что бот жив."""
    return web.Response(text="OK")


async def run_bot() -> None:
    """Основной цикл polling."""
    offset = None
    last_update_id = 0

    while True:
        try:
            updates = await get_updates(offset)
            
            for update in updates:
                last_update_id = update.get("update_id", last_update_id) + 1
                offset = last_update_id
                await handle_message(update)

            await asyncio.sleep(0.5)

        except asyncio.CancelledError:
            logger.info("Bot stopped")
            break
        except Exception as e:
            logger.error(f"Polling error: {e}")
            await asyncio.sleep(1)


def start_bot():
    """Запуск бота (в отдельном потоке)."""
    if not BOT_TOKEN:
        logger.error("❌ Не найден BOT_TOKEN в переменных окружения!")
        raise ValueError("Missing BOT_TOKEN")

    if not CHUTES_API_KEY:
        logger.warning("⚠️ CHUTES_API_KEY не установлен — AI не будет работать")

    logger.info("🚀 Бот запущен! Подключено к Telegram и Chutes AI")
    asyncio.run(run_bot())


def main():
    """Запуск HTTP-сервера + polling в потоке."""
    if not BOT_TOKEN:
        logger.error("❌ Не найден BOT_TOKEN в переменных окружения!")
        raise ValueError("Missing BOT_TOKEN")

    logger.info("🚀 Telegram бот запущен! Порт: %s", PORT)

    app = web.Application()
    app.router.add_get("/", health_check)

    # Сбрасываем webhook перед polling
    asyncio.create_task(delete_webhook())

    # Запускаем polling в отдельном потоке
    import threading
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()

    # Запускаем HTTP-сервер
    web.run_app(app, host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    main()
