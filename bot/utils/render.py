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
    cost = card.get('cost', 0)
    move_cost = card.get('move_cost', 1)
    
    keywords = card.get('keywords', '')
    kw_icons = ''
    for kw, icon in KEYWORD_ICONS.items():
        if kw in keywords:
            kw_icons += f' {icon}'
    
    stats = f"{attack}⚔️{health}❤️"
    if armor > 0:
        stats += f"{armor}🛡️"
    
    return f"{kingdom_symbol}{rarity_color}{name}({stats}){kw_icons} {cost}🧪{move_cost}👣"


def render_hp_bar(current: int, max_hp: int = STARTING_HP) -> str:
    """Шкала здоровья"""
    filled = "❤️" * current
    empty = "🖤" * (max_hp - current)
    return f"{filled}{empty}"


def render_ecotone_owner(ecotone: List) -> str:
    """Определение владельца экотона для отображения"""
    has_player = any(slot and slot['owner'] == 'player' for slot in ecotone)
    has_bot = any(slot and slot['owner'] == 'bot' for slot in ecotone)
    
    if has_player and has_bot:
        return "⚔️"
    elif has_player:
        return "👤"
    elif has_bot:
        return "🤖"
    else:
        return "⚔️"


def render_field(game: Dict[str, Any], user_id: int) -> str:
    """Отрисовка игрового поля — компактный режим"""
    
    is_player_turn = game.get('is_player_turn', True)
    player_field = game.get('player_field', {'back': []})
    bot_field = game.get('bot_field', {'back': []})
    ecotone = game.get('ecotone', [])
    player_hand = game.get('player_hand', [])
    player_deck = game.get('player_deck', [])
    bot_deck = game.get('bot_deck', [])
    
    lines = []
    
    # Строка 1: заголовок
    primary = game.get('player_kingdom', '')
    secondary = game.get('player_secondary_kingdom', '')
    p_sym = KINGDOM_SYMBOLS.get(primary, '')
    s_sym = KINGDOM_SYMBOLS.get(secondary, '')
    
    turn_str = "👤" if is_player_turn else "⏳"
    lines.append(
        f"🧬Р{game.get('round_number', 1)} "
        f"🧪{game.get('current_atp', 1)} "
        f"{turn_str} "
        f"{p_sym}{s_sym} "
        f"📚{len(player_deck)}vs{len(bot_deck)}"
    )
    
    # Строка 2: МО противника (одной строкой)
    bot_back = bot_field.get('back', [])
    bot_parts = []
    for i in range(MAX_BACK_ROW):
        if i < len(bot_back) and bot_back[i]:
            if bot_back[i].get('is_planet'):
                hp = bot_back[i].get('health', STARTING_HP)
                bot_parts.append(f"🪐{hp}")
            else:
                c = bot_back[i]
                bot_parts.append(f"{c.get('emoji','🃏')}{c.get('attack',0)}⚔️{c.get('health',0)}❤️")
        else:
            bot_parts.append("⬜")
    lines.append("🤖" + "|".join(bot_parts))
    
    # Строка 3: Экотон (одной строкой)
    eco_owner = render_ecotone_owner(ecotone)
    eco_parts = []
    for i in range(MAX_LBS):
        if i < len(ecotone) and ecotone[i]:
            slot_data = ecotone[i]
            c = slot_data['card']
            owner_icon = "👤" if slot_data['owner'] == 'player' else "🤖"
            eco_parts.append(f"{owner_icon}{c.get('emoji','🃏')}{c.get('attack',0)}⚔️{c.get('health',0)}❤️")
        else:
            eco_parts.append("⬜")
    lines.append(f"{eco_owner}" + "|".join(eco_parts))
    
    # Строка 4: МО игрока (одной строкой)
    player_back = player_field.get('back', [])
    player_parts = []
    for i in range(MAX_BACK_ROW):
        if i < len(player_back) and player_back[i]:
            if player_back[i].get('is_planet'):
                hp = game.get('player_planet_health', STARTING_HP)
                player_parts.append(f"🌎{hp}")
            else:
                c = player_back[i]
                player_parts.append(f"{c.get('emoji','🃏')}{c.get('attack',0)}⚔️{c.get('health',0)}❤️")
        else:
            player_parts.append("⬜")
    lines.append("👤" + "|".join(player_parts))
    
    # Строка 5: Рука (одной строкой, кратко)
    if player_hand:
        hand_parts = []
        for i, card in enumerate(player_hand):
            hand_parts.append(
                f"[{i+1}]{card.get('emoji','🃏')}{card.get('name','')}"
                f"({card.get('cost',0)}🧪)"
            )
        lines.append("📋" + " ".join(hand_parts))
    
    # Строка 6: Лог (только последнее событие)
    log = game.get('log', [])
    if log:
        last_entry = log[-1]
        # Обрезаем длинные логи
        if len(last_entry) > 80:
            last_entry = last_entry[:77] + "..."
        lines.append(f"📜{last_entry}")
    
    return "\n".join(lines)