# bot/handlers/start.py
from aiogram import Router, types
from aiogram.filters import Command
from bot.utils.database import load_game
start_router = Router()
@start_router.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    
    text = (
        "🧬 <b>Добро пожаловать в МУТАЦИЯ!</b>\n\n"
        "Генетическая карточная стратегия. Вы управляете эволюцией.\n\n"
        "🌍 <b>Выберите своё царство:</b>\n"
        "🐾 Animalia — сила и хищничество\n"
        "🌿 Plantae — защита и регенерация\n"
        "🍄 Fungi — паразитизм и контроль\n"
        "🦠 Bacteria — мутации и токсины\n\n"
        "⚔️ Нажмите <b>/newgame</b> чтобы начать битву!"
    )
    
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="🧬 Новая игра")],
            [types.KeyboardButton(text="📖 Правила")],
        ],
        resize_keyboard=True
    )
    
    await message.answer(text, parse_mode="HTML", reply_markup=keyboard)
@start_router.message(lambda message: message.text == "🧬 Новая игра")
async def cmd_new_game_shortcut(message: types.Message):
    await cmd_new_game(message)
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
@start_router.message(lambda message: message.text == "📖 Правила")
async def cmd_rules(message: types.Message):
    text = (
        "📖 <b>Правила игры «МУТАЦИЯ»</b>\n\n"
        "🎯 <b>Цель:</b> Уничтожить планету противника (10 HP).\n\n"
        "⚡ <b>Мутагены:</b>\n"
        "• В начале хода вы получаете Мутагены = номер раунда\n"
        "• Неиспользованные Мутагены сгорают\n\n"
        "🃏 <b>Карты:</b>\n"
        "• У вас 20 карт в колоде\n"
        "• В начале игры вы получаете 4 карты\n"
        "• Каждый ход вы добираете 1 карту\n\n"
        "🏛️ <b>Поле:</b>\n"
        "• МО (4 слота) — для защиты\n"
        "• Экотон (4 слота) — для атаки\n\n"
        "⚔️ <b>Бой:</b>\n"
        "• Урон = Атака − Броня\n"
        "• Дистанционная атака — из МО\n"
        "• Охрана — защищает соседей\n\n"
        "Удачи, эволюционер! 🧬"
    )
    
    await message.answer(text, parse_mode="HTML")