# bot/index.py — корневой файл для Yandex Cloud Functions
import json
import logging
import asyncio
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

# Хранилище последнего обработанного update_id
_last_update_id = 0


async def process_updates():
    """Получает новые сообщения из Telegram через long polling и обрабатывает их."""
    global _last_update_id

    try:
        # Получаем обновления от Telegram (исходящее соединение — работает!)
        offset = _last_update_id + 1 if _last_update_id else None
        updates = await bot.get_updates(
            offset=offset,
            timeout=10,
            allowed_updates=["message", "callback_query"]
        )

        for update in updates:
            update_id = update.update_id
            if update_id > _last_update_id:
                _last_update_id = update_id
                logger.info(f"Получено обновление: {update_id}")
                await dp.feed_update(bot, update)

        return len(updates)
    except Exception as e:
        logger.error(f"Ошибка при получении обновлений: {e}")
        return 0


# Функция-обработчик для Yandex Cloud Functions
async def handler(event, context):
    """
    Точка входа для Yandex Cloud Functions.
    При вызове по HTTP (GET) — проверка работоспособности.
    При вызове по триггеру — long polling.
    """
    try:
        # GET-запрос — просто проверка работоспособности
        if event.get('httpMethod') == 'GET':
            return {
                'statusCode': 200,
                'body': json.dumps({'status': 'ok', 'message': 'Bot is running'})
            }

        # Проверка на вызов от Timer Trigger
        # Timer Trigger отправляет POST с телом {"messages": [...]}
        # или просто пустой запрос
        body = event.get('body', '')
        if body:
            try:
                body_data = json.loads(body)
                # Если это сообщение от Telegram (вебхук) — обрабатываем
                if 'update_id' in body_data:
                    update = Update(**body_data)
                    await dp.feed_update(bot, update)
                    return {
                        'statusCode': 200,
                        'body': json.dumps({'status': 'ok'})
                    }
            except json.JSONDecodeError:
                pass

        # Long polling: получаем новые сообщения из Telegram
        processed = await process_updates()
        logger.info(f"Обработано обновлений: {processed}")

        return {
            'statusCode': 200,
            'body': json.dumps({'status': 'ok', 'processed': processed})
        }
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }