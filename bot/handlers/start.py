# bot/handlers/start.py
from aiogram import Router, types
from aiogram.filters import Command
from bot.utils.database import load_game, delete_game

start_router = Router()


@start_router.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    
    text = (
        "🧬 <b>Добро пожаловать в ГЕНОМНЫЕ ВОЙНЫ!</b>\n\n"
        "Генетическая карточная стратегия. Вы управляете эволюцией.\n\n"
        "🌍 <b>Выберите своё царство:</b>\n"
        "🐾 Animalia — сила и хищничество\n"
        "🌿 Plantae — защита и регенерация\n"
        "🍄 Fungi — паразитизм и контроль\n"
        "🦠 Bacteria — мутации и токсины\n\n"
        "⚔️ Нажмите <b>/newgame</b> чтобы начать битву!"
    )
    
    await message.answer(text, parse_mode="HTML")


@start_router.message(Command("newgame"))
async def cmd_new_game(message: types.Message):
    """Обработчик команды /newgame — выбор царства"""
    
    text = "🌍 <b>Выберите своё царство:</b>"
    
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="🐾 Animalia", callback_data="kingdom_Animalia"),
                types.InlineKeyboardButton(text="🌿 Plantae", callback_data="kingdom_Plantae")
            ],
            [
                types.InlineKeyboardButton(text="🍄 Fungi", callback_data="kingdom_Fungi"),
                types.InlineKeyboardButton(text="🦠 Bacteria", callback_data="kingdom_Bacteria")
            ],
            [types.InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
        ]
    )
    
    await message.answer(text, parse_mode="HTML", reply_markup=keyboard)


@start_router.message(Command("rules"))
async def cmd_rules(message: types.Message):
    """Обработчик команды /rules — правила игры"""
    text = (
        "📖 <b>Правила игры «ГЕНОМНЫЕ ВОЙНЫ»</b>\n\n"
        "🎯 <b>Цель:</b> Уничтожить планету противника (10 HP).\n\n"
        "⚡ <b>Мутагены:</b>\n"
        "• В начале хода вы получаете Мутагены = номер раунда\n"
        "• Неиспользованные Мутагены сгорают\n\n"
        "🃏 <b>Карты:</b>\n"
        "• У вас 20 карт в колоде\n"
        "• В начале игры вы получаете 4 карты\n"
        "• Каждый ход вы добираете 1 карту\n\n"
        "🏛️ <b>Поле:</b>\n"
        "• Место Обитания (4 слота) — для защиты\n"
        "• Экотон (4 слота) — для атаки\n\n"
        "⚔️ <b>Бой:</b>\n"
        "• Урон = Атака − Броня\n"
        "• Дистанционная атака — из Места Обитания\n"
        "• Охрана — защищает соседей\n\n"
        "Удачи, эволюционер! 🧬"
    )
    
    await message.answer(text, parse_mode="HTML")


@start_router.message(Command("help"))
async def cmd_help(message: types.Message):
    """Обработчик команды /help — правила игры"""
    await cmd_rules(message)


@start_router.message(Command("endgame"))
async def cmd_end_game(message: types.Message):
    """Обработчик команды /endgame — завершить игру"""
    delete_game(message.from_user.id)
    await message.answer("✅ Игра завершена. Начни новую: /newgame")


@start_router.message(Command("genome"))
async def cmd_genome(message: types.Message):
    """Обработчик команды /genome — древо геномов (заглушка)"""
    await message.answer(
        "🌿 <b>Древо геномов</b>\n\n"
        "Показывает прогресс в каждом царстве.\n"
        "Функция в разработке.",
        parse_mode="HTML"
    )


@start_router.message(Command("clean"))
async def cmd_clean(message: types.Message):
    """Обработчик команды /clean — очистка чата"""
    await message.delete()
    msg = await message.answer("🧹 Чат очищен!")
    await msg.delete()