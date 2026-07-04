import os
from dotenv import load_dotenv
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env файле")

# В Yandex Cloud Functions можно писать только в /tmp
if os.path.exists('/tmp'):
    DATABASE_PATH = '/tmp/gmo.db'
else:
    DATABASE_PATH = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        'data', 
        'gmo.db'
    )

# Настройки игры
STARTING_HP = 10
MAX_CARDS_IN_DECK = 20
MAX_HAND_SIZE = 4
MAX_ATP = 10
MAX_BACK_ROW = 4
MAX_LBS = 4
PLANET_SLOT = 3