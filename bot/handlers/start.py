# bot/handlers/start.py
from aiogram import Router, types
from aiogram.filters import Command
start_router = Router()
@start_router.message(Command("start"))
async def cmd_start(message: types.Message):
    text = (
        "🧬 <b>Добро пожаловать в ГМО!</b>\n\n"
        "Генетическая карточная стратегия.\n\n"
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
@start_router.message(Command("newgame"))
async def cmd_new_game(message: types.Message):
    text = "🌍 <b>Выберите своё царство:</b>"
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="🦁 Animalia", callback_data="kingdom_Animalia"),
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
@start_router.callback_query(lambda c: c.data.startswith("kingdom_"))
async def callback_choose_kingdom(callback: types.CallbackQuery):
    kingdom = callback.data.replace("kingdom_", "")
    await callback.message.delete()
    await callback.answer(f"Выбрано: {kingdom}")
    await callback.message.answer(f"✅ Выбрано царство: {kingdom}")
@start_router.callback_query(lambda c: c.data == "cancel")
async def callback_cancel(callback: types.CallbackQuery):
    await callback.message.delete()
    await callback.answer("Отменено")
