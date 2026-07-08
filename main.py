import logging
import os
import aiohttp
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ========================================
# ЭТАП 1: Загрузка переменных окружения
# ========================================
# .env файл содержит чувствительные данные (токены, ключи)
# и не должен попадать в git-репозиторий
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
# Chutes API использует OpenAI-compatible формат запросов
# Это значит, что мы отправляем те же payload, что и в OpenAI API
CHUTES_API_URL = os.getenv("CHUTES_API_URL", "https://llm.chutes.ai/v1/chat/completions")
CHUTES_API_KEY = os.getenv("CHUTES_API_KEY", "")
MODEL_NAME = os.getenv("MODEL_NAME", "default-model")

# ========================================
# ЭТАП 4: Хранилище истории диалога
# ========================================
# Словарь: user_id -> список сообщений (контекст беседы)
# Позволяет боту "помнить" предыдущие сообщения
chat_histories: dict[int, list[dict]] = {}


# ========================================
# ЭТАП 5: Функция обращения к Chutes AI
# ========================================
async def get_ai_response(user_message: str) -> str:
    """
    Отправляет сообщение в Chutes API и получает ответ.
    
    Использует OpenAI-compatible формат:
    - endpoint: /v1/chat/completions
    - payload: {model, messages, max_tokens, temperature}
    - auth: Bearer token через заголовок Authorization
    
    Args:
        user_message: Текст сообщения от пользователя
        
    Returns:
        Ответ от AI или текст ошибки
    """
    # Формируем историю диалога для контекста
    # Chutes API принимает messages в формате:
    # [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    messages = [
        {"role": "system", "content": "Ты полезный ассистент. Отвечай на русском языке кратко и по делу."},
        *chat_histories.get(0, []),  # Используем user_id=0 как глобальный контекст
        {"role": "user", "content": user_message},
    ]

    # Формируем HTTP-запрос к Chutes API
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
        # Используем aiohttp для асинхронного запроса
        async with aiohttp.ClientSession() as session:
            async with session.post(CHUTES_API_URL, json=payload, headers=headers) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    logger.error(f"Chutes API error: {resp.status} - {error_text}")
                    return "😅 Произошла ошибка при обработке запроса. Попробуй позже."
                
                data = await resp.json()
                
                # Извлекаем ответ из стандартного формата OpenAI
                # Структура: {"choices": [{"message": {"content": "..."}}]}
                assistant_message = data["choices"][0]["message"]["content"]
                
                # Обновляем историю диалога (сохраняем контекст)
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
# ЭТАП 6: Обработчики Telegram-команд
# ========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /start
    Приветствует пользователя и объясняет возможности бота
    """
    user = update.effective_user
    await update.message.reply_html(
        f"Привет, {user.mention_html()}! 👋\n\n"
        f"Я чат-бот с AI от Chutes. "
        f"Напиши мне что-нибудь, и я отвечу! 🤖"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /help
    Показывает справку по использованию
    """
    await update.message.reply_text(
        "📖 Справка:\n\n"
        "• Просто пиши сообщения — я отвечу с помощью AI\n"
        "• /start — начать общение\n"
        "• /help — показать эту справку"
    )


async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    ОБРАБОТЧИК СООБЩЕНИЙ — заменяет старый echo()
    
    1. Получает текст от пользователя
    2. Отправляет его в Chutes AI
    3. Возвращает ответ от AI
    """
    user_message = update.message.text
    user_id = update.effective_user.id
    
    logger.info(f"Сообщение от @{user_id}: {user_message}")
    
    # Отправляем индикатор "печатает..."
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing",  # Показывает анимацию набора текста
    )
    
    # Получаем ответ от AI
    ai_response = await get_ai_response(user_message)
    
    # Отправляем ответ пользователю
    await update.message.reply_text(ai_response, parse_mode="HTML")


# ========================================
# ЭТАП 7: Точка входа — запуск бота
# ========================================
def main() -> None:
    """
    Настройка и запуск Telegram-бота:
    1. Проверяем обязательные переменные окружения
    2. Создаём Application из python-telegram-bot
    3. Регистрируем обработчики команд и сообщений
    4. Запускаем polling (опрос серверов Telegram)
    """
    # Проверка обязательных переменных
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TELEGRAM_BOT_TOKEN:
        logger.error("❌ Не найден TELEGRAM_BOT_TOKEN в переменных окружения!")
        logger.error("Создай .env файл с TELEGRAM_BOT_TOKEN='твой_токен'")
        raise ValueError("Missing TELEGRAM_BOT_TOKEN")

    if not CHUTES_API_KEY:
        logger.warning("⚠️ CHUTES_API_KEY не установлен — AI не будет работать")
        logger.warning("Бот будет отвечать эхом. Настрой ключ в .env")
    
    # Создаём приложение
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Регистрируем обработчики:
    # /start — приветствие
    app.add_handler(CommandHandler("start", start))
    
    # /help — справка
    app.add_handler(CommandHandler("help", help_command))
    
    # Все обычные текстовые сообщения (не команды) -> AI-ответ
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_handler))
    
    # Запуск бота
    logger.info("🚀 Бот запущен! Подключено к Telegram и Chutes AI")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
