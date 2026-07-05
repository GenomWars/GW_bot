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
    """Обработчик команды /newgame — выбор основного царства"""
    
    text = "🌍 <b>Выберите ОСНОВНОЕ царство:</b>"
    
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="🐾 Animalia", callback_data="primary_Animalia"),
                types.InlineKeyboardButton(text="🌿 Plantae", callback_data="primary_Plantae")
            ],
            [
                types.InlineKeyboardButton(text="🍄 Fungi", callback_data="primary_Fungi"),
                types.InlineKeyboardButton(text="🦠 Bacteria", callback_data="primary_Bacteria")
            ],
            [types.InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")],
            [types.InlineKeyboardButton(text="ℹ️ О царствах", callback_data="kingdom_info")]
        ]
    )
    
    await message.answer(text, parse_mode="HTML", reply_markup=keyboard)


@start_router.callback_query(lambda c: c.data == "kingdom_info")
async def callback_kingdom_info(callback: types.CallbackQuery):
    """Информация о царствах"""
    
    text = (
        "🌍 <b>О царствах</b>\n\n"
        "Вы выбираете <b>основное</b> и <b>второстепенное</b> царства.\n\n"
        "🐾 <b>Animalia</b> — сила и хищничество\n"
        "  • Агрессивные существа с высоким уроном\n\n"
        "🌿 <b>Plantae</b> — защита и регенерация\n"
        "  • Крепкая броня и охрана союзников\n\n"
        "🍄 <b>Fungi</b> — паразитизм и контроль\n"
        "  • Живучесть и контроль поля\n\n"
        "🦠 <b>Bacteria</b> — мутации и токсины\n"
        "  • Дистанционные атаки и яды\n\n"
        "Основное царство даёт больше карт в колоду.\n"
        "Второстепенное добавляет разнообразие."
    )
    
    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()


@start_router.callback_query(lambda c: c.data == "cancel")
async def callback_cancel(callback: types.CallbackQuery):
    """Отмена выбора"""
    await callback.message.delete()
    await callback.answer("❌ Отменено!")


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
        "• Дистанционная атака — без ответного урона\n"
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


@start_router.message(Command("clear"))
async def cmd_clear(message: types.Message):
    """Обработчик команды /clear — очистка чата"""
    await message.delete()
    msg = await message.answer("🧹 Чат очищен!")
    await msg.delete()