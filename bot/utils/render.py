# bot/utils/render.py
from typing import Dict, Any, List
from bot.config import MAX_BACK_ROW, MAX_LBS, STARTING_HP

# Символы царств
KINGDOM_SYMBOLS = {
    'Animalia': '🐾',
    'Plantae': '🌿',
    'Fungi': '🍄',
    'Bacteria': '🦠',
}

# Цвета редкости
RARITY_COLORS = {
    'Common': '⚪',
    'Rare': '🟢',
}

# Иконки ключевых слов
KEYWORD_ICONS = {
    'Дистанционная атака': '🏹',
    'Охрана': '🛡️',
}


def render_rarity_color(rarity: str) -> str:
    """Цветовая индикация редкости"""
    return RARITY_COLORS.get(rarity, '⚪')


def render_kingdom_symbol(kingdom: str) -> str:
    """Символ царства"""
    return KINGDOM_SYMBOLS.get(kingdom, '🃏')


def render_card_short(card: Dict[str, Any]) -> str:
    """Краткое отображение карты"""
    rarity_color = render_rarity_color(card.get('rarity', 'Common'))
    kingdom_symbol = render_kingdom_symbol(card.get('kingdom', ''))
    name = card.get('name', 'Карта')
    attack = card.get('attack', 0)
    health = card.get('health', 0)
    armor = card.get('armor', 0)
    
    keywords = card.get('keywords', '')
    kw_icons = ''
    for kw, icon in KEYWORD_ICONS.items():
        if kw in keywords:
            kw_icons += f' {icon}'
    
    armor_str = f'/{armor}' if armor > 0 else ''
    
    return f"{kingdom_symbol} {rarity_color} {name} ({attack}/{health}{armor_str}){kw_icons}"


def render_hp_bar(current: int, max_hp: int = STARTING_HP) -> str:
    """Шкала здоровья"""
    filled = "❤️" * current
    empty = "🖤" * (max_hp - current)
    return f"{filled}{empty}"


def render_field(game: Dict[str, Any], user_id: int) -> str:
    """Отрисовка игрового поля"""
    
    is_player_turn = game.get('is_player_turn', True)
    player_field = game.get('player_field', {'back': [], 'lbs': []})
    bot_field = game.get('bot_field', {'back': [], 'lbs': []})
    player_hand = game.get('player_hand', [])
    
    lines = []
    
    # Заголовок
    turn_str = "👤 Твой ход" if is_player_turn else "⏳ Ход противника"
    lines.append(f"🧬 ГЕНОМНЫЕ ВОЙНЫ — Раунд {game.get('round_number', 1)} | 🧪 Мутагены: {game.get('current_atp', 1)} | {turn_str}")
    lines.append("")
    
    # Место Обитания противника (4 слота)
    lines.append("🌿 МЕСТО ОБИТАНИЯ ПРОТИВНИКА:")
    bot_back = bot_field.get('back', [])
    for i in range(MAX_BACK_ROW):
        if i < len(bot_back) and bot_back[i]:
            if bot_back[i].get('is_planet'):
                hp = bot_back[i].get('health', STARTING_HP)
                lines.append(f"  [{i+1}] 🪐 ПЛАНЕТА ({hp}/{STARTING_HP})")
            else:
                lines.append(f"  [{i+1}] {render_card_short(bot_back[i])}")
        else:
            lines.append(f"  [{i+1}] ⬜")
    lines.append("")
    
    # Экотон (горизонтально)
    lines.append("⚔️ ЭКОТОН:")
    lbs = player_field.get('lbs', [])
    eco_parts = []
    for i in range(MAX_LBS):
        if i < len(lbs) and lbs[i]:
            eco_parts.append(f"[{i+1}] {render_card_short(lbs[i])}")
        else:
            eco_parts.append(f"[{i+1}] ⬜")
    lines.append("  " + " | ".join(eco_parts))
    lines.append("")
    
    # Место Обитания игрока
    lines.append("🌿 ТВОЁ МЕСТО ОБИТАНИЯ:")
    player_back = player_field.get('back', [])
    for i in range(MAX_BACK_ROW):
        if i < len(player_back) and player_back[i]:
            if player_back[i].get('is_planet'):
                hp = game.get('player_planet_health', STARTING_HP)
                lines.append(f"  [{i+1}] 🌎 ТВОЯ ПЛАНЕТА ({hp}/{STARTING_HP})")
            else:
                lines.append(f"  [{i+1}] {render_card_short(player_back[i])}")
        else:
            lines.append(f"  [{i+1}] ⬜")
    lines.append("")
    
    # Рука игрока
    lines.append("📋 ТВОЯ РУКА:")
    for i, card in enumerate(player_hand):
        rarity_color = render_rarity_color(card.get('rarity', 'Common'))
        kingdom_symbol = render_kingdom_symbol(card.get('kingdom', ''))
        name = card.get('name', 'Карта')
        attack = card.get('attack', 0)
        health = card.get('health', 0)
        armor = card.get('armor', 0)
        cost = card.get('cost', 0)
        keywords = card.get('keywords', '')
        
        kw_icons = ''
        for kw, icon in KEYWORD_ICONS.items():
            if kw in keywords:
                kw_icons += f' {icon}'
        
        armor_str = f'/{armor}' if armor > 0 else ''
        
        lines.append(f"  [{i+1}] {kingdom_symbol} {rarity_color} {name} ({attack}/{health}{armor_str}){kw_icons} — {cost} 🧪")
    lines.append("")
    
    # Лог
    log = game.get('log', [])
    if log:
        lines.append("📜 ЛОГ:")
        for entry in log[-3:]:
            lines.append(f"  • {entry}")
    
    return "\n".join(lines)