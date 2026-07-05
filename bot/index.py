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


async def long_poll():
    """Долгий long polling — ждём сообщения до 25 секунд."""
    global _last_update_id

    total_processed = 0
    start_time = asyncio.get_event_loop().time()

    # Делаем несколько циклов, пока не выйдет время
    while asyncio.get_event_loop().time() - start_time < 25:
        try:
            offset = _last_update_id + 1 if _last_update_id else None
            updates = await bot.get_updates(
                offset=offset,
                timeout=15,  # Ждём новые сообщения до 15 секунд
                allowed_updates=["message", "callback_query"]
            )

            for update in updates:
                update_id = update.update_id
                if update_id > _last_update_id:
                    _last_update_id = update_id
                    logger.info(f"Получено обновление: {update_id}")
                    await dp.feed_update(bot, update)
                    total_processed += 1

            # Если сообщений нет — выходим, чтобы не тратить время
            if not updates:
                break

        except Exception as e:
            logger.error(f"Ошибка при получении обновлений: {e}")
            break

    return total_processed


# Функция-обработчик для Yandex Cloud Functions
async def handler(event, context):
    """
    Точка входа для Yandex Cloud Functions.
    При вызове по HTTP (GET) — проверка работоспособности.
    При вызове по триггеру — долгий long polling.
    """
    try:
        # GET-запрос — просто проверка работоспособности
        if event.get('httpMethod') == 'GET':
            return {
                'statusCode': 200,
                'body': json.dumps({'status': 'ok', 'message': 'Bot is running'})
            }

        # Проверка на сообщение от Telegram (на случай если вебхук ещё активен)
        body = event.get('body', '')
        if body:
            try:
                body_data = json.loads(body)
                if 'update_id' in body_data:
                    update = Update(**body_data)
                    await dp.feed_update(bot, update)
                    return {
                        'statusCode': 200,
                        'body': json.dumps({'status': 'ok'})
                    }
            except json.JSONDecodeError:
                pass

        # Долгий long polling — ждём сообщения до 25 секунд
        processed = await long_poll()
        if processed:
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