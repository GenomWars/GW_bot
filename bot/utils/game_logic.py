# bot/utils/game_logic.py
import random
from typing import Dict, Any, List, Optional, Tuple
from bot.config import STARTING_HP, MAX_ATP, MAX_BACK_ROW, MAX_LBS, PLANET_SLOT
from bot.utils.cards import create_deck, shuffle_deck, draw_card


# ─── ИНИЦИАЛИЗАЦИЯ ИГРЫ ───────────────────────────────────────────────

def init_game(primary_kingdom: str, secondary_kingdom: str) -> Dict[str, Any]:
    """Инициализация новой игры с основным и второстепенным царством"""

    kingdoms = ['Animalia', 'Plantae', 'Fungi', 'Bacteria']
    available = [k for k in kingdoms if k != primary_kingdom and k != secondary_kingdom]
    bot_primary = random.choice(available)
    bot_secondary = random.choice([k for k in available if k != bot_primary])

    player_deck = create_deck(primary_kingdom, secondary_kingdom)
    bot_deck = create_deck(bot_primary, bot_secondary)
    shuffle_deck(player_deck)
    shuffle_deck(bot_deck)

    player_hand = []
    bot_hand = []
    for _ in range(4):
        card, player_deck = draw_card(player_deck)
        if card:
            player_hand.append(card)
        card, bot_deck = draw_card(bot_deck)
        if card:
            bot_hand.append(card)

    player_field = {'back': [None] * MAX_BACK_ROW}
    bot_field = {'back': [None] * MAX_BACK_ROW}

    player_field['back'][PLANET_SLOT] = {
        'is_planet': True, 'health': STARTING_HP, 'max_health': STARTING_HP, 'owner': 'player'
    }
    bot_field['back'][PLANET_SLOT] = {
        'is_planet': True, 'health': STARTING_HP, 'max_health': STARTING_HP, 'owner': 'bot'
    }

    ecotone = [None] * MAX_LBS
    is_player_turn = random.choice([True, False])

    game = {
        'player_kingdom': primary_kingdom,
        'player_secondary_kingdom': secondary_kingdom,
        'bot_kingdom': bot_primary,
        'bot_secondary_kingdom': bot_secondary,
        'player_deck': player_deck,
        'bot_deck': bot_deck,
        'player_hand': player_hand,
        'bot_hand': bot_hand,
        'player_field': player_field,
        'bot_field': bot_field,
        'ecotone': ecotone,
        'player_planet_health': STARTING_HP,
        'bot_planet_health': STARTING_HP,
        'round_number': 1,
        'current_atp': 0,
        'is_player_turn': is_player_turn,
        'bot_moved_this_round': False,
        'game_over': False,
        'log': [],
        'player_deck_empty_rounds': 0,
        'bot_deck_empty_rounds': 0,
    }

    if is_player_turn:
        game['current_atp'] = min(1, MAX_ATP)
        game['log'].append("👤 Ты ходишь первым!")
    else:
        game['log'].append("🤖 Противник ходит первым")

    return game


# ─── ХОД ИГРОКА ────────────────────────────────────────────────────────

def start_player_turn(game: Dict[str, Any]) -> Dict[str, Any]:
    """Начало хода игрока: мутагены = номер раунда (сгорают), добор карты."""

    round_num = game['round_number']
    game['current_atp'] = min(round_num, MAX_ATP)

    card, game['player_deck'] = draw_card(game['player_deck'])
    if card:
        game['player_hand'].append(card)
        game['log'].append(f"📩 Взята карта: {card.get('emoji', '🃏')} {card.get('name', '')}")
    else:
        game = apply_deck_exhaustion_damage(game, 'player')

    game['is_player_turn'] = True
    game['log'].append(f"🧪 Получено {game['current_atp']} мутагенов (раунд {round_num})")
    return game


# ─── ХОД БОТА ──────────────────────────────────────────────────────────

def bot_turn(game: Dict[str, Any]) -> Dict[str, Any]:
    """Ход бота: добор карты, разыгрывание, перемещение, атака."""

    if game.get('game_over', False):
        return game

    round_num = game['round_number']
    bot_atp = min(round_num, MAX_ATP)

    # Добор карты
    card, game['bot_deck'] = draw_card(game['bot_deck'])
    if card:
        game['bot_hand'].append(card)
    else:
        game = apply_deck_exhaustion_damage(game, 'bot')

    # Разыгрывание карт (дорогие сначала)
    for card_data in sorted(game['bot_hand'], key=lambda c: c.get('cost', 0), reverse=True):
        if bot_atp <= 0:
            break
        cost = card_data.get('cost', 0)
        if cost > bot_atp:
            continue
        for slot in range(MAX_BACK_ROW):
            if slot == PLANET_SLOT:
                continue
            if game['bot_field']['back'][slot] is None:
                game['bot_field']['back'][slot] = card_data
                bot_atp -= cost
                game['bot_hand'].remove(card_data)
                game['log'].append(f"🤖 Противник разыграл {card_data.get('emoji', '🃏')} {card_data.get('name', '')} (слот {slot + 1})")
                break

    # Перемещение в экотон
    for slot in range(MAX_BACK_ROW):
        if slot == PLANET_SLOT:
            continue
        creature = game['bot_field']['back'][slot]
        if creature and not creature.get('is_planet'):
            move_cost = creature.get('move_cost', 1)
            if bot_atp >= move_cost:
                for eco_slot in range(MAX_LBS):
                    if game['ecotone'][eco_slot] is None:
                        game['ecotone'][eco_slot] = {'owner': 'bot', 'card': creature}
                        game['bot_field']['back'][slot] = None
                        bot_atp -= move_cost
                        game['log'].append(f"🤖 Противник переместил {creature.get('emoji', '🃏')} {creature.get('name', '')} в экотон")
                        break

    # Атака (3 приоритета)
    _bot_attack(game)

    return check_game_over(game)


def _bot_attack(game: Dict[str, Any]) -> None:
    """Логика атаки бота (модифицирует game in-place)."""
    attacked = False
    player_back = game['player_field']['back']

    # 1. Из экотона → МО игрока
    for eco_slot in range(MAX_LBS):
        if attacked:
            return
        slot_data = game['ecotone'][eco_slot]
        if slot_data and slot_data['owner'] == 'bot':
            guard_slot = _find_guard(player_back)
            target = guard_slot if guard_slot is not None else PLANET_SLOT
            perform_attack(game, 'ecotone', eco_slot, 'mo', target, 'bot')
            attacked = True

    # 2. Из МО → экотон (если есть цели)
    if not attacked:
        for slot in range(MAX_BACK_ROW):
            if attacked:
                return
            if slot == PLANET_SLOT:
                continue
            creature = game['bot_field']['back'][slot]
            if creature and not creature.get('is_planet'):
                for eco_slot in range(MAX_LBS):
                    eco_data = game['ecotone'][eco_slot]
                    if eco_data and eco_data['owner'] == 'player':
                        perform_attack(game, 'mo', slot, 'ecotone', eco_slot, 'bot')
                        attacked = True
                        break

    # 3. Дистанционная из МО → МО
    if not attacked:
        for slot in range(MAX_BACK_ROW):
            if attacked:
                return
            if slot == PLANET_SLOT:
                continue
            creature = game['bot_field']['back'][slot]
            if creature and not creature.get('is_planet') and 'Дистанционная атака' in creature.get('keywords', ''):
                guard_slot = _find_guard(player_back)
                target = guard_slot if guard_slot is not None else PLANET_SLOT
                perform_attack(game, 'mo', slot, 'mo', target, 'bot')
                attacked = True


# ─── РАЗМЕЩЕНИЕ КАРТЫ ─────────────────────────────────────────────────

def place_card_on_field(game: Dict[str, Any], card_index: int, slot: int) -> Dict[str, Any]:
    """Размещение карты из руки в указанный слот Места Обитания."""

    if slot == PLANET_SLOT:
        return {'error': '❌ Нельзя разместить карту на слоте планеты!'}

    hand = game.get('player_hand', [])
    if card_index >= len(hand):
        return {'error': '❌ Карта не найдена!'}

    card = hand[card_index]
    cost = card.get('cost', 0)
    current_atp = game.get('current_atp', 0)

    if cost > current_atp:
        return {'error': f'❌ Недостаточно мутагенов! Нужно {cost}, есть {current_atp}'}

    field = game.get('player_field', {'back': [None] * MAX_BACK_ROW})
    if field['back'][slot] is not None:
        return {'error': '❌ Слот занят!'}

    field['back'][slot] = card
    game['player_hand'].pop(card_index)
    game['current_atp'] -= cost
    game['log'].append(f"🃏 Разыграна {card.get('emoji', '🃏')} {card.get('name', '')} в слот {slot + 1}")
    return {'success': True}


# ─── ПЕРЕМЕЩЕНИЕ В ЭКОТОН ─────────────────────────────────────────────

def move_to_ecotone(game: Dict[str, Any], slot: int) -> Dict[str, Any]:
    """Перемещение существа из Места Обитания в Экотон."""

    if slot == PLANET_SLOT:
        game['log'].append('❌ Нельзя переместить планету в экотон!')
        return game

    field = game.get('player_field', {'back': [None] * MAX_BACK_ROW})
    creature = field['back'][slot]

    if creature is None or creature.get('is_planet'):
        game['log'].append(f'❌ Нет существа в слоте {slot + 1} для перемещения')
        return game

    move_cost = creature.get('move_cost', 1)
    current_atp = game.get('current_atp', 0)

    if move_cost > current_atp:
        game['log'].append(f'❌ Недостаточно мутагенов для перемещения! Нужно {move_cost}')
        return game

    ecotone = game.get('ecotone', [None] * MAX_LBS)
    for eco_slot in range(MAX_LBS):
        if ecotone[eco_slot] is None:
            ecotone[eco_slot] = {'owner': 'player', 'card': creature}
            field['back'][slot] = None
            game['current_atp'] -= move_cost
            game['ecotone'] = ecotone
            game['log'].append(f"🚀 {creature.get('emoji', '🃏')} {creature.get('name', '')} перемещён в экотон (слот {eco_slot + 1})")
            return game

    game['log'].append('❌ Нет свободных слотов в экотоне!')
    return game


# ─── БОЕВАЯ СИСТЕМА ───────────────────────────────────────────────────

def _find_guard(field_back: List) -> Optional[int]:
    """Поиск существа с Охраной."""
    for slot in range(MAX_BACK_ROW):
        if slot == PLANET_SLOT:
            continue
        creature = field_back[slot]
        if creature and 'Охрана' in creature.get('keywords', ''):
            return slot
    return None


def _deal_damage(creature: Dict[str, Any], damage: int) -> bool:
    """Нанести урон существу. True — уничтожено."""
    creature['health'] = creature.get('health', 0) - damage
    return creature['health'] <= 0


def _get_creature(game: Dict[str, Any], zone: str, slot: int, owner: str) -> Optional[Dict]:
    """Получить существо из зоны. owner='player'|'bot'."""
    if zone == 'ecotone':
        ecotone = game.get('ecotone', [])
        if slot < len(ecotone) and ecotone[slot] and ecotone[slot]['owner'] == owner:
            return ecotone[slot]['card']
    elif zone == 'mo':
        field_key = 'player_field' if owner == 'player' else 'bot_field'
        field = game.get(field_key, {'back': [None] * MAX_BACK_ROW})
        if slot < len(field['back']) and field['back'][slot] and not field['back'][slot].get('is_planet'):
            return field['back'][slot]
    return None


def _remove_creature(game: Dict[str, Any], zone: str, slot: int, owner: str) -> None:
    """Удалить существо из зоны."""
    if zone == 'ecotone':
        game['ecotone'][slot] = None
    elif zone == 'mo':
        field_key = 'player_field' if owner == 'player' else 'bot_field'
        game[field_key]['back'][slot] = None


def perform_attack(
    game: Dict[str, Any],
    attacker_zone: str,
    attacker_slot: int,
    target_zone: str,
    target_slot: int,
    attacker_owner: str = 'player'
) -> Dict[str, Any]:
    """Выполнение атаки.

    Правила:
    - Обычные: экотон↔МО — оба получают урон.
    - Дистанционные: МО→МО — без ответного урона.
      В остальных случаях (МО→экотон, экотон→МО) — получают ответ.
    - Урон = Атака − Броня цели.
    - Ответный урон = Атака цели − Броня атакующего.
    """

    # Атакующий
    attacker = _get_creature(game, attacker_zone, attacker_slot, attacker_owner)
    if not attacker:
        return game

    attack = attacker.get('attack', 0)
    is_ranged = 'Дистанционная атака' in attacker.get('keywords', '')
    is_close_combat = not (is_ranged and attacker_zone == 'mo' and target_zone == 'mo')

    # Цель
    if target_zone == 'mo':
        enemy_owner = 'bot' if attacker_owner == 'player' else 'player'
        field_key = 'bot_field' if attacker_owner == 'player' else 'player_field'
        field = game[field_key]['back']

        if target_slot >= len(field) or field[target_slot] is None:
            return game

        target = field[target_slot]

        # Атака на планету — проверка Охраны
        if target.get('is_planet'):
            guard_slot = _find_guard(field)
            if guard_slot is not None:
                target = field[guard_slot]
                target_slot = guard_slot
                game['log'].append(f"🛡️ Охрана! Атака перенаправлена на {target.get('emoji', '🃏')} {target.get('name', '')}")

            if target.get('is_planet'):
                damage = max(0, attack)
                game[f'{enemy_owner}_planet_health'] = max(0, game[f'{enemy_owner}_planet_health'] - damage)
                game['log'].append(f"⚔️ {attacker.get('emoji', '🃏')} {attacker.get('name', '')} атакует планету — {damage} урона!")
                is_close_combat = False
            else:
                _attack_creature(game, attacker, target, attack, field, target_slot)
        else:
            _attack_creature(game, attacker, target, attack, field, target_slot)

    elif target_zone == 'ecotone':
        ecotone = game.get('ecotone', [])
        if target_slot >= len(ecotone) or ecotone[target_slot] is None:
            return game

        target_data = ecotone[target_slot]
        enemy_owner = 'bot' if attacker_owner == 'player' else 'player'
        if target_data['owner'] != enemy_owner:
            return game

        target_creature = target_data['card']
        armor = target_creature.get('armor', 0)
        damage = max(0, attack - armor)
        destroyed = _deal_damage(target_creature, damage)
        game['log'].append(f"⚔️ {attacker.get('emoji', '🃏')} атакует {target_creature.get('emoji', '🃏')} ({target_creature.get('name', '')}) в экотоне — {damage} урона (броня {armor})")
        if destroyed:
            ecotone[target_slot] = None
            game['log'].append(f"💀 {target_creature.get('emoji', '🃏')} {target_creature.get('name', '')} уничтожен!")

        # Ответный урон
        if is_close_combat and not destroyed:
            _counter_attack(game, target_creature, attacker, attacker_zone, attacker_slot, attacker_owner)
    else:
        return game

    return game


def _attack_creature(game, attacker, target, attack, field, target_slot):
    """Атака существа в МО."""
    armor = target.get('armor', 0)
    damage = max(0, attack - armor)
    destroyed = _deal_damage(target, damage)
    game['log'].append(f"⚔️ {attacker.get('emoji', '🃏')} атакует {target.get('emoji', '🃏')} ({target.get('name', '')}) — {damage} урона (броня {armor})")
    if destroyed:
        field[target_slot] = None
        game['log'].append(f"💀 {target.get('emoji', '🃏')} {target.get('name', '')} уничтожен!")


def _counter_attack(game, target_creature, attacker, attacker_zone, attacker_slot, attacker_owner):
    """Ответный урон."""
    target_attack = target_creature.get('attack', 0)
    if target_attack <= 0:
        return

    attacker_armor = attacker.get('armor', 0)
    counter_damage = max(0, target_attack - attacker_armor)
    if counter_damage <= 0:
        return

    destroyed = _deal_damage(attacker, counter_damage)
    game['log'].append(f"↩️ {target_creature.get('emoji', '🃏')} {target_creature.get('name', '')} наносит ответный урон {attacker.get('emoji', '🃏')} {attacker.get('name', '')} — {counter_damage}")
    if destroyed:
        _remove_creature(game, attacker_zone, attacker_slot, attacker_owner)
        game['log'].append(f"💀 {attacker.get('emoji', '🃏')} {attacker.get('name', '')} уничтожен!")


# ─── ПРОВЕРКА ЗАВЕРШЕНИЯ ──────────────────────────────────────────────

def check_game_over(game: Dict[str, Any]) -> Dict[str, Any]:
    """Проверка завершения игры. Возвращает game (всегда truthy).
    Используйте game['game_over'] для проверки."""

    if game.get('player_planet_health', STARTING_HP) <= 0:
        game['game_over'] = True
        game['log'].append('😵 Твоя планета уничтожена! Ты проиграл!')

    if game.get('bot_planet_health', STARTING_HP) <= 0:
        game['game_over'] = True
        game['log'].append('🏆 Планета противника уничтожена! Ты победил!')

    return game


# ─── УРОН ОТ ИСТОЩЕНИЯ КОЛОДЫ ─────────────────────────────────────────

def apply_deck_exhaustion_damage(game: Dict[str, Any], target: str) -> Dict[str, Any]:
    """Урон от истощения коло��ы: 1, 2, 3... за каждый пустой добор."""

    if target == 'player' and not game['player_deck']:
        game['player_deck_empty_rounds'] += 1
        damage = game['player_deck_empty_rounds']
        game['player_planet_health'] = max(0, game['player_planet_health'] - damage)
        game['log'].append(f'💀 Твоя колода пуста! Планета получает {damage} урона')
    elif target == 'bot' and not game['bot_deck']:
        game['bot_deck_empty_rounds'] += 1
        damage = game['bot_deck_empty_rounds']
        game['bot_planet_health'] = max(0, game['bot_planet_health'] - damage)
        game['log'].append(f'💀 Колода противника пуста! Его планета получает {damage} урона')

    return game


# ─── ВСПОМОГАТЕЛЬНАЯ: ЗАВЕРШЕНИЕ ХОДА ─────────────────────────────────

def end_round_after_attack(game: Dict[str, Any]) -> Dict[str, Any]:
    """Завершить раунд после атаки: ход бота → новый раунд → ход игрока."""
    game = bot_turn(game)
    game['bot_moved_this_round'] = True

    if game['game_over']:
        return game

    game['round_number'] += 1
    game['bot_moved_this_round'] = False
    game = start_player_turn(game)
    return game