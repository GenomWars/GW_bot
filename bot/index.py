# bot/index.py — корневой файл для Yandex Cloud Functions
import json
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Update
from bot.config import BOT_TOKEN
from bot.handlers.start import start_router
from bot.handlers.game import game_router
from bot.utils.database import init_database, seed_cards

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация базы данных (при первом запуске)
init_database()
seed_cards()

# Создаём бота и диспетчер
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()
dp.include_router(start_router)
dp.include_router(game_router)


# Функция-обработчик для Yandex Cloud Functions
async def handler(event, context):
    """
    Точка входа для Yandex Cloud Functions.
    Принимает HTTP-запрос от Telegram (POST) и передаёт его в aiogram.
    """
    try:
        # GET-запрос — просто проверка работоспособности
        if event.get('httpMethod') == 'GET':
            return {
                'statusCode': 200,
                'body': json.dumps({'status': 'ok', 'message': 'Bot is running'})
            }

        # Парсим тело запроса (Telegram отправляет JSON)
        body = event.get('body', '')
        if not body:
            return {
                'statusCode': 200,
                'body': json.dumps({'status': 'ok'})
            }

        body = json.loads(body)
        logger.info(f"Получено обновление: {body}")

        # Создаём объект Update
        update = Update(**body)

        # Передаём обновление в диспетчер
        await dp.feed_update(bot, update)

        return {
            'statusCode': 200,
            'body': json.dumps({'status': 'ok'})
        }
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }