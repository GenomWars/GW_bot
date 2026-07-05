# bot/handlers/game.py
from aiogram import Router, types
from aiogram.filters import Command
from bot.utils.database import load_game, save_game, delete_game
from bot.utils.game_logic import (
    init_game, place_card_on_field, move_to_ecotone,
    perform_attack, bot_turn, check_game_over,
    start_player_turn, end_round_after_attack
)
from bot.utils.render import render_field
from bot.keyboards.game import (
    create_game_keyboard, create_slot_keyboard,
    create_attacker_keyboard, create_target_keyboard
)

game_router = Router()


# ─── ВЫБОР ЦАРСТВ ─────────────────────────────────────────────────────

@game_router.callback_query(lambda c: c.data.startswith("primary_"))
async def callback_choose_primary(callback: types.CallbackQuery):
    primary = callback.data.replace("primary_", "")

    existing = load_game(callback.from_user.id)
    if existing and not existing.get('game_over', False):
        await callback.answer("У тебя уже есть активная игра!")
        await callback.message.answer("⚠️ Закончи текущую игру командой /endgame")
        return

    kingdoms = ['Animalia', 'Plantae', 'Fungi', 'Bacteria']
    available = [k for k in kingdoms if k != primary]

    text = f"🌍 <b>Основное царство:</b> {primary}\n\nТеперь выберите <b>ВТОРОСТЕПЕННОЕ</b> царство:"
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(
                text=f"{'🐾' if k == 'Animalia' else '🌿' if k == 'Plantae' else '🍄' if k == 'Fungi' else '🦠'} {k}",
                callback_data=f"secondary_{primary}_{k}"
            )]
            for k in available
        ] + [[types.InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]]
    )

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer()


@game_router.callback_query(lambda c: c.data.startswith("secondary_"))
async def callback_choose_secondary(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    primary, secondary = parts[1], parts[2]

    game = init_game(primary, secondary)

    if not game['is_player_turn']:
        bot_turn(game)
        game['bot_moved_this_round'] = True
        start_player_turn(game)

    save_game(callback.from_user.id, game)

    text = render_field(game)
    keyboard = create_game_keyboard(game)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer(f"✅ Игра начата! {primary} + {secondary}")


# ─── РАЗМЕЩЕНИЕ КАРТЫ ─────────────────────────────────────────────────

@game_router.callback_query(lambda c: c.data.startswith("play_card_"))
async def callback_play_card(callback: types.CallbackQuery):
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

    keyboard = create_slot_keyboard("place", card_index)
    await callback.message.edit_text(text="🎯 Выберите слот для размещения карты:", reply_markup=keyboard)
    await callback.answer()


@game_router.callback_query(lambda c: c.data.startswith("place_slot_"))
async def callback_place_slot(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    card_index, slot = int(parts[2]), int(parts[3])

    game = load_game(callback.from_user.id)
    if not game:
        await callback.answer("Игра не найдена!")
        return

    result = place_card_on_field(game, card_index, slot)
    if result.get("error"):
        await callback.answer(result["error"])
        return

    save_game(callback.from_user.id, game)
    text = render_field(game)
    keyboard = create_game_keyboard(game)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer("✅ Карта размещена!")


# ─── АТАКА ─────────────────────────────────────────────────────────────

@game_router.callback_query(lambda c: c.data == "action_attack")
async def callback_attack(callback: types.CallbackQuery):
    game = load_game(callback.from_user.id)
    if not game:
        await callback.answer("Игра не найдена!")
        return

    keyboard = create_attacker_keyboard(game)
    await callback.message.edit_text(text="⚔️ Выберите существо для атаки:", reply_markup=keyboard)
    await callback.answer()


@game_router.callback_query(lambda c: c.data.startswith("attack_sel_"))
async def callback_attack_select_attacker(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    zone, slot = parts[2], int(parts[3])
    attacker_zone = 'ecotone' if zone == 'eco' else 'mo'

    game = load_game(callback.from_user.id)
    if not game:
        await callback.answer("Игра не найдена!")
        return

    keyboard = create_target_keyboard(game, attacker_zone, slot)
    await callback.message.edit_text(text="🎯 Выберите цель для атаки:", reply_markup=keyboard)
    await callback.answer()


@game_router.callback_query(lambda c: c.data.startswith("attack_tgt_"))
async def callback_attack_execute(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    att_zone = 'ecotone' if parts[2] == 'eco' else 'mo'
    att_slot = int(parts[3])
    tgt_zone = 'mo' if parts[4] == 'mo' else 'ecotone'
    tgt_slot = int(parts[5])

    game = load_game(callback.from_user.id)
    if not game:
        await callback.answer("Игра не найдена!")
        return

    game = perform_attack(game, att_zone, att_slot, tgt_zone, tgt_slot)
    save_game(callback.from_user.id, game)

    if game['game_over']:
        text = render_field(game)
        keyboard = create_game_keyboard(game)
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
        await callback.answer("🏆 Игра завершена!")
        return

    game = end_round_after_attack(game)
    save_game(callback.from_user.id, game)

    if game['game_over']:
        text = render_field(game)
        keyboard = create_game_keyboard(game)
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
        await callback.answer("😵 Вы проиграли!")
        return

    text = render_field(game)
    keyboard = create_game_keyboard(game)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer("⚔️ Атака выполнена!")


# ─── ПЕРЕМЕЩЕНИЕ В ЭКОТОН ─────────────────────────────────────────────

@game_router.callback_query(lambda c: c.data == "action_move")
async def callback_move(callback: types.CallbackQuery):
    game = load_game(callback.from_user.id)
    if not game:
        await callback.answer("Игра не найдена!")
        return

    keyboard = create_slot_keyboard("move", 0)
    await callback.message.edit_text(text="🎯 Выберите слот с существом для перемещения в экотон:", reply_markup=keyboard)
    await callback.answer()


@game_router.callback_query(lambda c: c.data.startswith("move_slot_"))
async def callback_move_slot(callback: types.CallbackQuery):
    slot = int(callback.data.split("_")[3])

    game = load_game(callback.from_user.id)
    if not game:
        await callback.answer("Игра не найдена!")
        return

    game = move_to_ecotone(game, slot)
    save_game(callback.from_user.id, game)

    text = render_field(game)
    keyboard = create_game_keyboard(game)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer("🚀 Карта перемещена в экотон!")


# ─── ЗАВЕРШЕНИЕ ХОДА ──────────────────────────────────────────────────

@game_router.callback_query(lambda c: c.data == "action_end_turn")
async def callback_end_turn(callback: types.CallbackQuery):
    game = load_game(callback.from_user.id)
    if not game:
        await callback.answer("Игра не найдена!")
        return

    if game.get('bot_moved_this_round', False):
        game['round_number'] += 1
        game['bot_moved_this_round'] = False
        start_player_turn(game)
        save_game(callback.from_user.id, game)

        text = render_field(game)
        keyboard = create_game_keyboard(game)
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
        await callback.answer("⏭️ Раунд завершён!")
    else:
        game = bot_turn(game)
        game['bot_moved_this_round'] = True
        save_game(callback.from_user.id, game)

        if game['game_over']:
            text = render_field(game)
            keyboard = create_game_keyboard(game)
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
            await callback.answer("😵 Вы проиграли!")
            return

        game['round_number'] += 1
        game['bot_moved_this_round'] = False
        start_player_turn(game)
        save_game(callback.from_user.id, game)

        text = render_field(game)
        keyboard = create_game_keyboard(game)
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
        await callback.answer("⏭️ Ход завершён!")


# ─── ОБНОВЛЕНИЕ / ОТМЕНА ──────────────────────────────────────────────

@game_router.callback_query(lambda c: c.data == "action_refresh")
async def callback_refresh(callback: types.CallbackQuery):
    game = load_game(callback.from_user.id)
    if not game:
        await callback.answer("Игра не найдена!")
        return

    text = render_field(game)
    keyboard = create_game_keyboard(game)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer("🔄 Поле обновлено!")


@game_router.callback_query(lambda c: c.data == "action_cancel")
async def callback_cancel(callback: types.CallbackQuery):
    game = load_game(callback.from_user.id)
    if not game:
        await callback.answer("Игра не найдена!")
        return

    text = render_field(game)
    keyboard = create_game_keyboard(game)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer("❌ Отменено!")


# ─── ПЕРЕЗАПУСК / ЗАГЛУШКА ────────────────────────────────────────────

@game_router.callback_query(lambda c: c.data == "game_restart")
async def callback_restart(callback: types.CallbackQuery):
    delete_game(callback.from_user.id)
    await callback.message.delete()
    await callback.message.answer("🔄 Начните новую игру: /newgame")
    await callback.answer()


@game_router.callback_query(lambda c: c.data == "dummy")
async def callback_dummy(callback: types.CallbackQuery):
    await callback.answer("⏳ Подождите...")