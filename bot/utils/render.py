# bot/utils/render.py
from typing import Dict, Any, List
from bot.config import MAX_BACK_ROW, MAX_LBS, STARTING_HP

KINGDOM_SYMBOLS = {
    'Animalia': '🐾', 'Plantae': '🌿', 'Fungi': '🍄', 'Bacteria': '🦠',
}


def render_card_short(card: Dict[str, Any]) -> str:
    """Краткое отображение карты для клавиатур."""
    kingdom_symbol = KINGDOM_SYMBOLS.get(card.get('kingdom', ''), '🃏')
    name = card.get('name', 'Карта')
    attack = card.get('attack', 0)
    health = card.get('health', 0)
    armor = card.get('armor', 0)
    cost = card.get('cost', 0)
    move_cost = card.get('move_cost', 1)

    stats = f"{attack}⚔️{health}❤️"
    if armor > 0:
        stats += f"{armor}🛡️"

    kw_icons = ''
    keywords = card.get('keywords', '')
    if 'Дистанционная атака' in keywords:
        kw_icons += ' 🏹'
    if 'Охрана' in keywords:
        kw_icons += ' 🛡️'

    return f"{kingdom_symbol}{name}({stats}){kw_icons} {cost}🧪{move_cost}👣"


def render_field(game: Dict[str, Any]) -> str:
    """Отрисовка игрового поля — компактный режим (6 строк)."""

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
    lines.append(f"🧬Р{game.get('round_number', 1)} 🧪{game.get('current_atp', 1)} {turn_str} {p_sym}{s_sym} 📚{len(player_deck)}vs{len(bot_deck)}")

    # Строка 2: МО противника
    bot_back = bot_field.get('back', [])
    bot_parts = []
    for i in range(MAX_BACK_ROW):
        if i < len(bot_back) and bot_back[i]:
            if bot_back[i].get('is_planet'):
                bot_parts.append(f"🪐{bot_back[i].get('health', STARTING_HP)}")
            else:
                c = bot_back[i]
                bot_parts.append(f"{c.get('emoji','🃏')}{c.get('attack',0)}⚔️{c.get('health',0)}❤️")
        else:
            bot_parts.append("⬜")
    lines.append("🤖" + "|".join(bot_parts))

    # Строка 3: Экотон
    has_player = any(s and s['owner'] == 'player' for s in ecotone)
    has_bot = any(s and s['owner'] == 'bot' for s in ecotone)
    eco_owner = "⚔️" if (has_player and has_bot) or (not has_player and not has_bot) else ("👤" if has_player else "🤖")

    eco_parts = []
    for i in range(MAX_LBS):
        if i < len(ecotone) and ecotone[i]:
            sd = ecotone[i]
            c = sd['card']
            owner_icon = "👤" if sd['owner'] == 'player' else "🤖"
            eco_parts.append(f"{owner_icon}{c.get('emoji','🃏')}{c.get('attack',0)}⚔️{c.get('health',0)}❤️")
        else:
            eco_parts.append("⬜")
    lines.append(f"{eco_owner}" + "|".join(eco_parts))

    # Строка 4: МО игрока
    player_back = player_field.get('back', [])
    player_parts = []
    for i in range(MAX_BACK_ROW):
        if i < len(player_back) and player_back[i]:
            if player_back[i].get('is_planet'):
                player_parts.append(f"🌎{game.get('player_planet_health', STARTING_HP)}")
            else:
                c = player_back[i]
                player_parts.append(f"{c.get('emoji','🃏')}{c.get('attack',0)}⚔️{c.get('health',0)}❤️")
        else:
            player_parts.append("⬜")
    lines.append("👤" + "|".join(player_parts))

    # Строка 5: Рука
    if player_hand:
        hand_parts = []
        for i, card in enumerate(player_hand):
            hand_parts.append(f"[{i+1}]{card.get('emoji','🃏')}{card.get('name','')}({card.get('cost',0)}🧪)")
        lines.append("📋" + " ".join(hand_parts))

    # Строка 6: Последний лог
    log = game.get('log', [])
    if log:
        last_entry = log[-1]
        if len(last_entry) > 80:
            last_entry = last_entry[:77] + "..."
        lines.append(f"📜{last_entry}")

    return "\n".join(lines)