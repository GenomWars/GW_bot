# bot/keyboards/game.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Dict, Any
from bot.config import MAX_BACK_ROW
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
        keyboard.append([
            InlineKeyboardButton(
                text=f"🃏 {card['emoji']} {card['name']} ({card['cost']} 🧪 | {card.get('move_cost', 1)} 👣)",
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
    """Клавиатура для выбора слота"""
    
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