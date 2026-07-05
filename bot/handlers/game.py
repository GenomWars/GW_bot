# bot/handlers/game.py
from aiogram import Router, types
from aiogram.filters import Command
from bot.utils.database import load_game, save_game, delete_game
from bot.utils.game_logic import init_game, place_card_on_field, move_to_ecotone, perform_attack, bot_turn, check_game_over, start_player_turn
from bot.utils.render import render_field
from bot.keyboards.game import create_game_keyboard, create_slot_keyboard

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
    
    # Если бот ходит первым — сразу делаем его ход
    if not game['is_player_turn']:
        bot_turn(game)
        game['bot_moved_this_round'] = True
        # После хода бота передаём ход игроку
        game['is_first_turn_of_game'] = False
        start_player_turn(game)
    
    save_game(callback.from_user.id, game)
    
    await callback.message.delete()
    
    text = render_field(game, callback.from_user.id)
    keyboard = create_game_keyboard(game)
    
    await callback.answer(f"✅ Игра начата! Царство: {kingdom}")
    await callback.message.answer(text, parse_mode="HTML", reply_markup=keyboard)


@game_router.callback_query(lambda c: c.data.startswith("play_card_"))
async def callback_play_card(callback: types.CallbackQuery):
    """Обработчик выбора карты из руки для размещения"""
    
    card_index = int(callback.data.split("_")[2])
    game = load_game(callback.from_user.id)
    
    if not game or game.get('game_over', False):
        await callback.answer("Игра не найдена или завершена!")
        return
    
    if not game.get('is_player_turn', True):
        await callback.answer("Сейчас не твой ход!")
        return
    
    hand = game.get('player_hand', [])
    if card_index >= len(hand):
        await callback.answer("Карта не найдена!")
        return
    
    card = hand[card_index]
    cost = card.get('cost', 1)
    current_atp = game.get('current_atp', 0)
    
    if cost > current_atp:
        await callback.answer(f"❌ Недостаточно мутагенов! Нужно {cost}, есть {current_atp}")
        return
    
    # Показываем выбор слота для размещения
    keyboard = create_slot_keyboard("place", card_index)
    await callback.message.edit_text(
        text="🎯 Выберите слот для размещения карты:",
        reply_markup=keyboard
    )
    await callback.answer()


@game_router.callback_query(lambda c: c.data.startswith("place_slot_"))
async def callback_place_slot(callback: types.CallbackQuery):
    """Обработчик выбора слота для размещения карты"""
    
    parts = callback.data.split("_")
    card_index = int(parts[2])
    slot = int(parts[3])
    
    game = load_game(callback.from_user.id)
    if not game:
        await callback.answer("Игра не найдена!")
        return
    
    result = place_card_on_field(game, card_index, slot)
    
    if result.get("error"):
        await callback.answer(result["error"])
        return
    
    save_game(callback.from_user.id, game)
    
    text = render_field(game, callback.from_user.id)
    keyboard = create_game_keyboard(game)
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer("✅ Карта размещена!")


@game_router.callback_query(lambda c: c.data == "action_attack")
async def callback_attack(callback: types.CallbackQuery):
    """Обработчик атаки"""
    
    game = load_game(callback.from_user.id)
    if not game:
        await callback.answer("Игра не найдена!")
        return
    
    # Ищем первую карту в экотоне для атаки
    attacker_slot = None
    for i, card in enumerate(game['player_field']['lbs']):
        if card is not None:
            attacker_slot = i
            break
    
    if attacker_slot is None:
        await callback.answer("❌ Нет существ в экотоне для атаки!")
        return
    
    # Атакуем планету противника
    game = perform_attack(game, attacker_slot, 'planet')
    
    save_game(callback.from_user.id, game)
    
    # Проверка на завершение игры
    game_over = check_game_over(game)
    if game_over:
        text = render_field(game, callback.from_user.id)
        keyboard = create_game_keyboard(game)
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
        await callback.answer("🏆 Игра завершена!")
        return
    
    # Ход бота
    bot_turn(game)
    game['bot_moved_this_round'] = True
    save_game(callback.from_user.id, game)
    
    game_over = check_game_over(game)
    if game_over:
        text = render_field(game, callback.from_user.id)
        keyboard = create_game_keyboard(game)
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
        await callback.answer("😵 Вы проиграли!")
        return
    
    # Начинаем ход игрока
    start_player_turn(game)
    save_game(callback.from_user.id, game)
    
    text = render_field(game, callback.from_user.id)
    keyboard = create_game_keyboard(game)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer("⚔️ Атака выполнена!")


@game_router.callback_query(lambda c: c.data == "action_move")
async def callback_move(callback: types.CallbackQuery):
    """Обработчик перемещения в экотон"""
    
    game = load_game(callback.from_user.id)
    if not game:
        await callback.answer("Игра не найдена!")
        return
    
    # Показываем выбор существа для перемещения
    keyboard = create_slot_keyboard("move", 0)
    await callback.message.edit_text(
        text="🎯 Выберите слот с существом для перемещения в экотон:",
        reply_markup=keyboard
    )
    await callback.answer()


@game_router.callback_query(lambda c: c.data.startswith("move_slot_"))
async def callback_move_slot(callback: types.CallbackQuery):
    """Обработчик выбора слота для перемещения в экотон"""
    
    parts = callback.data.split("_")
    # callback_data = "move_slot_0_2" → ["move", "slot", "0", "2"]
    slot = int(parts[3])
    
    game = load_game(callback.from_user.id)
    if not game:
        await callback.answer("Игра не найдена!")
        return
    
    game = move_to_ecotone(game, slot)
    
    save_game(callback.from_user.id, game)
    
    text = render_field(game, callback.from_user.id)
    keyboard = create_game_keyboard(game)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer("🚀 Карта перемещена в экотон!")


@game_router.callback_query(lambda c: c.data == "action_end_turn")
async def callback_end_turn(callback: types.CallbackQuery):
    """Обработчик завершения хода"""
    
    game = load_game(callback.from_user.id)
    if not game:
        await callback.answer("Игра не найдена!")
        return
    
    # Снимаем флаг первого хода
    if game.get('is_first_turn_of_game', False):
        game['is_first_turn_of_game'] = False
    
    if game.get('bot_moved_this_round', False):
        # Бот уже ходил в этом раунде — игрок ходил вторым
        # Просто переходим к следующему раунду
        game['round_number'] += 1
        game['bot_moved_this_round'] = False
        
        # Начинаем ход игрока (добор карты + АТФ)
        start_player_turn(game)
        save_game(callback.from_user.id, game)
        
        text = render_field(game, callback.from_user.id)
        keyboard = create_game_keyboard(game)
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
        await callback.answer("⏭️ Раунд завершён!")
    else:
        # Бот ещё не ходил — игрок ходил первым
        # Сначала ход бота
        bot_turn(game)
        game['bot_moved_this_round'] = True
        save_game(callback.from_user.id, game)
        
        game_over = check_game_over(game)
        if game_over:
            text = render_field(game, callback.from_user.id)
            keyboard = create_game_keyboard(game)
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
            await callback.answer("😵 Вы проиграли!")
            return
        
        # Переходим к следующему раунду
        game['round_number'] += 1
        game['bot_moved_this_round'] = False
        
        # Начинаем ход игрока (добор карты + АТФ)
        start_player_turn(game)
        save_game(callback.from_user.id, game)
        
        text = render_field(game, callback.from_user.id)
        keyboard = create_game_keyboard(game)
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
        await callback.answer("⏭️ Ход завершён!")


@game_router.callback_query(lambda c: c.data == "action_refresh")
async def callback_refresh(callback: types.CallbackQuery):
    """Обработчик обновления поля"""
    
    game = load_game(callback.from_user.id)
    if not game:
        await callback.answer("Игра не найдена!")
        return
    
    text = render_field(game, callback.from_user.id)
    keyboard = create_game_keyboard(game)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer("🔄 Поле обновлено!")


@game_router.callback_query(lambda c: c.data == "action_cancel")
async def callback_cancel(callback: types.CallbackQuery):
    """Обработчик отмены"""
    
    game = load_game(callback.from_user.id)
    if not game:
        await callback.answer("Игра не найдена!")
        return
    
    text = render_field(game, callback.from_user.id)
    keyboard = create_game_keyboard(game)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer("❌ Отменено!")


@game_router.callback_query(lambda c: c.data == "game_restart")
async def callback_restart(callback: types.CallbackQuery):
    """Обработчик перезапуска игры"""
    
    delete_game(callback.from_user.id)
    await callback.message.delete()
    await callback.message.answer("🔄 Начните новую игру: /newgame")
    await callback.answer()


@game_router.callback_query(lambda c: c.data == "dummy")
async def callback_dummy(callback: types.CallbackQuery):
    """Заглушка для неактивных кнопок"""
    await callback.answer("⏳ Подождите...")


@game_router.message(Command("endgame"))
async def cmd_end_game(message: types.Message):
    """Завершение игры"""
    delete_game(message.from_user.id)
    await message.answer("✅ Игра завершена. Начни новую: /newgame")