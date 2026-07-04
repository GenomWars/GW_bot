# bot/handlers/game.py
from aiogram import Router, types
from aiogram.filters import Command
from bot.utils.database import load_game, save_game, delete_game
from bot.utils.game_logic import init_game, place_card_on_field, move_to_ecotone, perform_attack, bot_turn, check_game_over
from bot.utils.render import render_field
from bot.keyboards.game import create_game_keyboard

game_router = Router()

@game_router.callback_query(lambda c: c.data.startswith("kingdom_"))
async def callback_choose_kingdom(callback: types.CallbackQuery):
    """Обработчик выбора царства"""
    
    kingdom = callback.data.replace("kingdom_", "")
    
    existing = load_game(callback.from_user.id)
    if existing and not existing.get('game_over', False):
        await callback.answer("У тебя уже есть активная игра!")
        await callback.message.answer("⚠️ Закончи текущую игру командой /endgame")
        return
    
    game = init_game(kingdom)
    save_game(callback.from_user.id, game)
    
    await callback.message.delete()
    
    text = render_field(game, callback.from_user.id)
    keyboard = create_game_keyboard(game)
    
    await callback.answer(f"✅ Игра начата! Царство: {kingdom}")
    await callback.message.answer(text, parse_mode="HTML", reply_markup=keyboard)

@game_router.message(Command("endgame"))
async def cmd_end_game(message: types.Message):
    """Завершение игры"""
    delete_game(message.from_user.id)
    await message.answer("✅ Игра завершена. Начни новую: /newgame")