# bot/keyboards/game.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Dict, Any, List, Optional
from bot.config import MAX_BACK_ROW, MAX_LBS, PLANET_SLOT
from bot.utils.render import render_card_short


def create_game_keyboard(game: Dict[str, Any]) -> InlineKeyboardMarkup:
    """Создание клавиатуры для игры"""

    keyboard = []

    if game.get('game_over', False):
        keyboard.append([
            InlineKeyboardButton(text="🔄 Играть снова", callback_data="game_restart")
        ])
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    if not game.get('is_player_turn', True):
        keyboard.append([
            InlineKeyboardButton(text="⏳ Ход противника...", callback_data="dummy")
        ])
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    # Кнопки для карт в руке
    for i, card in enumerate(game.get('player_hand', [])):
        card_text = render_card_short(card)
        if len(card_text) > 64:
            card_text = f"{card['emoji']} {card['name']} ({card['cost']}🧪|{card.get('move_cost',1)}👣)"
        keyboard.append([
            InlineKeyboardButton(
                text=f"🃏 {card_text}",
                callback_data=f"play_card_{i}"
            )
        ])

    # Кнопки действий
    keyboard.append([
        InlineKeyboardButton(text="⚔️ Атаковать", callback_data="action_attack"),
        InlineKeyboardButton(text="🚀 В экотон", callback_data="action_move"),
    ])
    keyboard.append([
        InlineKeyboardButton(text="⏭️ Закончить ход", callback_data="action_end_turn"),
        InlineKeyboardButton(text="🔄 Обновить", callback_data="action_refresh"),
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def create_slot_keyboard(action: str, card_index: int) -> InlineKeyboardMarkup:
    """Клавиатура для выбора слота (размещение/перемещение)"""

    keyboard = []
    row = []
    for slot in range(MAX_BACK_ROW):
        row.append(InlineKeyboardButton(
            text=f"{slot+1}",
            callback_data=f"{action}_slot_{card_index}_{slot}"
        ))
        if len(row) == 4:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([
        InlineKeyboardButton(text="❌ Отмена", callback_data="action_cancel")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def create_attacker_keyboard(game: Dict[str, Any]) -> InlineKeyboardMarkup:
    """Клавиатура выбора атакующего существа"""

    keyboard = []

    # Существа в экотоне
    ecotone = game.get('ecotone', [])
    has_eco_attacker = False
    for i, slot_data in enumerate(ecotone):
        if slot_data and slot_data['owner'] == 'player':
            card = slot_data['card']
            has_eco_attacker = True
            card_text = f"⚔️ Экотон [{i+1}] {card.get('emoji', '🃏')} {card.get('name', '')}"
            if len(card_text) > 64:
                card_text = f"⚔️ Экотон [{i+1}] {card.get('emoji', '🃏')}"
            keyboard.append([
                InlineKeyboardButton(
                    text=card_text,
                    callback_data=f"attack_sel_eco_{i}"
                )
            ])

    # Существа в МО
    player_field = game.get('player_field', {'back': [None] * MAX_BACK_ROW})
    has_mo_attacker = False
    for i, creature in enumerate(player_field['back']):
        if i == PLANET_SLOT:
            continue
        if creature and not creature.get('is_planet'):
            has_enemy_in_eco = any(
                s and s['owner'] == 'bot' for s in ecotone
            )
            is_ranged = 'Дистанционная атака' in creature.get('keywords', '')
            if has_enemy_in_eco or is_ranged:
                has_mo_attacker = True
                card_text = f"🏠 МО [{i+1}] {creature.get('emoji', '🃏')} {creature.get('name', '')}"
                if len(card_text) > 64:
                    card_text = f"🏠 МО [{i+1}] {creature.get('emoji', '🃏')}"
                keyboard.append([
                    InlineKeyboardButton(
                        text=card_text,
                        callback_data=f"attack_sel_mo_{i}"
                    )
                ])

    if not has_eco_attacker and not has_mo_attacker:
        keyboard.append([
            InlineKeyboardButton(text="❌ Нет существ для атаки", callback_data="dummy")
        ])
    else:
        keyboard.append([
            InlineKeyboardButton(text="❌ Отмена", callback_data="action_cancel")
        ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def create_target_keyboard(
    game: Dict[str, Any],
    attacker_zone: str,
    attacker_slot: int
) -> InlineKeyboardMarkup:
    """Клавиатура выбора цели для атаки

    Формат callback_data: attack_tgt_{att_zone}_{att_slot}_{tgt_zone}_{tgt_slot}
    att_zone: 'eco' | 'mo'
    tgt_zone: 'mo' | 'eco'
    """

    att_zone_short = 'eco' if attacker_zone == 'ecotone' else 'mo'

    keyboard = []

    # --- Цели в МО противника ---
    bot_field = game.get('bot_field', {'back': [None] * MAX_BACK_ROW})
    keyboard.append([InlineKeyboardButton(
        text="🎯 МЕСТО ОБИТАНИЯ ПРОТИВНИКА:",
        callback_data="dummy"
    )])

    for i, creature in enumerate(bot_field['back']):
        if creature and creature.get('is_planet'):
            hp = creature.get('health', 10)
            keyboard.append([
                InlineKeyboardButton(
                    text=f"🪐 Планета ({hp}❤️)",
                    callback_data=f"attack_tgt_{att_zone_short}_{attacker_slot}_mo_{i}"
                )
            ])
        elif creature:
            card_text = f"{creature.get('emoji', '🃏')} {creature.get('name', '')}"
            if len(card_text) > 64:
                card_text = f"{creature.get('emoji', '🃏')} [{i+1}]"
            keyboard.append([
                InlineKeyboardButton(
                    text=f"🎯 {card_text}",
                    callback_data=f"attack_tgt_{att_zone_short}_{attacker_slot}_mo_{i}"
                )
            ])
        else:
            keyboard.append([
                InlineKeyboardButton(
                    text=f"⬜ Слот {i+1} (пусто)",
                    callback_data="dummy"
                )
            ])

    # --- Цели в экотоне (существа противника) ---
    ecotone = game.get('ecotone', [])
    has_enemy_eco = any(s and s['owner'] == 'bot' for s in ecotone)

    if has_enemy_eco:
        keyboard.append([InlineKeyboardButton(
            text="🎯 ЭКОТОН (существа противника):",
            callback_data="dummy"
        )])
        for i, slot_data in enumerate(ecotone):
            if slot_data and slot_data['owner'] == 'bot':
                card = slot_data['card']
                card_text = f"{card.get('emoji', '🃏')} {card.get('name', '')}"
                if len(card_text) > 64:
                    card_text = f"{card.get('emoji', '🃏')} [{i+1}]"
                keyboard.append([
                    InlineKeyboardButton(
                        text=f"🎯 {card_text}",
                        callback_data=f"attack_tgt_{att_zone_short}_{attacker_slot}_eco_{i}"
                    )
                ])

    keyboard.append([
        InlineKeyboardButton(text="❌ Отмена", callback_data="action_cancel")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)