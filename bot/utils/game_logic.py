# bot/utils/game_logic.py
import random
from typing import Dict, Any, List, Optional, Tuple
from bot.config import STARTING_HP, MAX_ATP, MAX_BACK_ROW, MAX_LBS, PLANET_SLOT
from bot.utils.cards import create_deck, shuffle_deck, draw_card


def init_game(kingdom: str) -> Dict[str, Any]:
    """Инициализация новой игры"""

    # Выбор случайного царства для бота (отличного от игрока)
    kingdoms = ['Animalia', 'Plantae', 'Fungi', 'Bacteria']
    bot_kingdom = random.choice([k for k in kingdoms if k != kingdom])

    # Создание и перемешивание колод
    player_deck = create_deck(kingdom)
    bot_deck = create_deck(bot_kingdom)
    shuffle_deck(player_deck)
    shuffle_deck(bot_deck)

    # Раздача начальных карт (по 4)
    player_hand = []
    bot_hand = []
    for _ in range(4):
        card, player_deck = draw_card(player_deck)
        if card:
            player_hand.append(card)
        card, bot_deck = draw_card(bot_deck)
        if card:
            bot_hand.append(card)

    # Создание полей с планетами
    player_field = {'back': [None] * MAX_BACK_ROW}
    bot_field = {'back': [None] * MAX_BACK_ROW}

    # Планеты на слоте PLANET_SLOT (индекс 3)
    player_field['back'][PLANET_SLOT] = {
        'is_planet': True,
        'health': STARTING_HP,
        'max_health': STARTING_HP,
        'owner': 'player'
    }
    bot_field['back'][PLANET_SLOT] = {
        'is_planet': True,
        'health': STARTING_HP,
        'max_health': STARTING_HP,
        'owner': 'bot'
    }

    # Экотон (4 слота)
    ecotone = [None] * MAX_LBS

    # Определяем, кто ходит первым (случайно)
    is_player_turn = random.choice([True, False])

    game = {
        'player_kingdom': kingdom,
        'bot_kingdom': bot_kingdom,
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
        'is_first_turn_of_game': True,
        'bot_moved_this_round': False,
        'game_over': False,
        'log': [],
        'player_deck_empty_rounds': 0,
        'bot_deck_empty_rounds': 0,
    }

    # Если игрок ходит первым — сразу выдаём мутагены за 1-й раунд
    if is_player_turn:
        game['current_atp'] = min(1, MAX_ATP)
        game['log'].append("👤 Ты ходишь первым!")
    else:
        game['log'].append("🤖 Противник ходит первым")

    return game


def start_player_turn(game: Dict[str, Any]) -> Dict[str, Any]:
    """Начало хода игрока: добор карты и получение мутагенов

    Мутагены = номер раунда (но не больше MAX_ATP = 10).
    Неиспользованные мутагены сгорают — устанавливаются заново.
    """

    round_num = game['round_number']

    # Неиспользованные мутагены сгорают, устанавливаем новые = номер раунда
    game['current_atp'] = min(round_num, MAX_ATP)

    # Добор 1 карты из колоды
    card, game['player_deck'] = draw_card(game['player_deck'])
    if card:
        game['player_hand'].append(card)
        game['log'].append(
            f"📩 Взята карта: {card.get('emoji', '🃏')} {card.get('name', '')}"
        )
    else:
        # Колода пуста — урон от истощения
        game = apply_deck_exhaustion_damage(game, 'player')

    game['is_player_turn'] = True
    game['log'].append(
        f"🧪 Получено {game['current_atp']} мутагенов (раунд {round_num})"
    )

    return game


def _find_guard(field_back: List) -> Optional[int]:
    """Поиск существа с Охраной в указанном поле"""
    for slot in range(MAX_BACK_ROW):
        if slot == PLANET_SLOT:
            continue
        creature = field_back[slot]
        if creature and 'Охрана' in creature.get('keywords', ''):
            return slot
    return None


def _deal_damage_to_creature(creature: Dict[str, Any], damage: int) -> bool:
    """Нанесение урона существу. Возвращает True, если существо уничтожено."""
    creature['health'] = creature.get('health', 0) - damage
    return creature['health'] <= 0


def perform_attack(
    game: Dict[str, Any],
    attacker_zone: str,
    attacker_slot: int,
    target_zone: str,
    target_slot: int
) -> Dict[str, Any]:
    """Выполнение атаки.

    attacker_zone: 'ecotone' | 'mo' — откуда атакует
    attacker_slot: индекс слота атакующего
    target_zone: 'mo' (МО противника) | 'ecotone'
    target_slot: индекс слота цели

    Правила боя:
    - Обычные: атакуют из экотона → МО или из МО → экотон. Оба получают урон.
    - Дистанционные: атакуют из МО → МО без ответного урона.
      В остальных случаях (МО→экотон, экотон→МО) — получают ответный урон.
    - Урон = Атака − Броня цели (минимум 0).
    - Ответный урон = Атака цели − Броня атакующего (минимум 0).
    """

    # --- Получаем атакующее существо ---
    if attacker_zone == 'ecotone':
        ecotone = game.get('ecotone', [])
        if attacker_slot >= len(ecotone) or ecotone[attacker_slot] is None:
            return game
        attacker_data = ecotone[attacker_slot]
        if attacker_data['owner'] != 'player':
            return game
        attacker_creature = attacker_data['card']
    elif attacker_zone == 'mo':
        field = game.get('player_field', {'back': [None] * MAX_BACK_ROW})
        if attacker_slot >= len(field['back']) or field['back'][attacker_slot] is None:
            return game
        attacker_creature = field['back'][attacker_slot]
        if attacker_creature.get('is_planet'):
            return game
    else:
        return game

    attack = attacker_creature.get('attack', 0)
    is_ranged = 'Дистанционная атака' in attacker_creature.get('keywords', '')

    # Ближний бой? (оба получают урон)
    # Дистанционная атака из МО в МО — единственный случай без ответного урона
    is_close_combat = not (is_ranged and attacker_zone == 'mo' and target_zone == 'mo')

    # --- Получаем цель ---
    if target_zone == 'mo':
        bot_back = game['bot_field']['back']
        if target_slot >= len(bot_back) or bot_back[target_slot] is None:
            return game

        target_data = bot_back[target_slot]

        if target_data.get('is_planet'):
            # Атака планеты — проверяем Охрану
            guard_slot = _find_guard(bot_back)
            if guard_slot is not None:
                target_data = bot_back[guard_slot]
                target_slot = guard_slot
                game['log'].append(
                    f"🛡️ Охрана! Атака перенаправлена на "
                    f"{target_data.get('emoji', '🃏')} {target_data.get('name', '')}"
                )

            if target_data.get('is_planet'):
                # Атакуем планету (охраны нет или планета)
                damage = max(0, attack)
                game['bot_planet_health'] = max(0, game['bot_planet_health'] - damage)
                game['log'].append(
                    f"⚔️ {attacker_creature.get('emoji', '🃏')} "
                    f"{attacker_creature.get('name', '')} "
                    f"атакует планету противника — {damage} урона!"
                )
                # Планета не наносит ответный урон
                is_close_combat = False
            else:
                # Атака на охраняющее существо
                armor = target_data.get('armor', 0)
                damage = max(0, attack - armor)
                destroyed = _deal_damage_to_creature(target_data, damage)
                game['log'].append(
                    f"⚔️ {attacker_creature.get('emoji', '🃏')} атакует "
                    f"{target_data.get('emoji', '🃏')} ({target_data.get('name', '')}) — "
                    f"{damage} урона (броня {armor})"
                )
                if destroyed:
                    bot_back[target_slot] = None
                    game['log'].append(
                        f"💀 {target_data.get('emoji', '🃏')} "
                        f"{target_data.get('name', '')} уничтожен!"
                    )
        else:
            # Атака существа в МО противника
            armor = target_data.get('armor', 0)
            damage = max(0, attack - armor)
            destroyed = _deal_damage_to_creature(target_data, damage)
            game['log'].append(
                f"⚔️ {attacker_creature.get('emoji', '🃏')} атакует "
                f"{target_data.get('emoji', '🃏')} ({target_data.get('name', '')}) — "
                f"{damage} урона (броня {armor})"
            )
            if destroyed:
                bot_back[target_slot] = None
                game['log'].append(
                    f"💀 {target_data.get('emoji', '🃏')} "
                    f"{target_data.get('name', '')} уничтожен!"
                )

    elif target_zone == 'ecotone':
        ecotone = game.get('ecotone', [])
        if target_slot >= len(ecotone) or ecotone[target_slot] is None:
            return game

        target_data = ecotone[target_slot]
        if target_data['owner'] == 'player':
            return game  # Нельзя атаковать своё существо

        target_creature = target_data['card']
        armor = target_creature.get('armor', 0)
        damage = max(0, attack - armor)
        destroyed = _deal_damage_to_creature(target_creature, damage)
        game['log'].append(
            f"⚔️ {attacker_creature.get('emoji', '🃏')} атакует "
            f"{target_creature.get('emoji', '🃏')} ({target_creature.get('name', '')}) "
            f"в экотоне — {damage} урона (броня {armor})"
        )
        if destroyed:
            ecotone[target_slot] = None
            game['log'].append(
                f"💀 {target_creature.get('emoji', '🃏')} "
                f"{target_creature.get('name', '')} уничтожен!"
            )
    else:
        return game

    # --- Ответный урон (только в ближнем бою) ---
    if is_close_combat:
        # Определяем атаку цели для ответного удара
        target_attack = 0
        target_emoji = ''
        target_name = ''

        if target_zone == 'mo':
            bot_back = game['bot_field']['back']
            if target_slot < len(bot_back) and bot_back[target_slot] is not None:
                t = bot_back[target_slot]
                if not t.get('is_planet'):
                    target_attack = t.get('attack', 0)
                    target_emoji = t.get('emoji', '🃏')
                    target_name = t.get('name', '')
        elif target_zone == 'ecotone':
            ecotone = game.get('ecotone', [])
            if target_slot < len(ecotone) and ecotone[target_slot] is not None:
                t = ecotone[target_slot]['card']
                target_attack = t.get('attack', 0)
                target_emoji = t.get('emoji', '🃏')
                target_name = t.get('name', '')

        if target_attack > 0:
            attacker_armor = attacker_creature.get('armor', 0)
            counter_damage = max(0, target_attack - attacker_armor)

            if counter_damage > 0:
                attacker_destroyed = _deal_damage_to_creature(attacker_creature, counter_damage)
                game['log'].append(
                    f"↩️ {target_emoji} {target_name} наносит ответный урон "
                    f"{attacker_creature.get('emoji', '🃏')} "
                    f"{attacker_creature.get('name', '')} — {counter_damage}"
                )
                if attacker_destroyed:
                    if attacker_zone == 'ecotone':
                        game['ecotone'][attacker_slot] = None
                    elif attacker_zone == 'mo':
                        game['player_field']['back'][attacker_slot] = None
                    game['log'].append(
                        f"💀 {attacker_creature.get('emoji', '🃏')} "
                        f"{attacker_creature.get('name', '')} уничтожен!"
                    )

    return game


def bot_turn(game: Dict[str, Any]) -> Dict[str, Any]:
    """Ход бота: добор карты, разыгрывание, перемещение, атака"""

    if game.get('game_over', False):
        return game

    round_num = game['round_number']
    bot_atp = min(round_num, MAX_ATP)  # Мутагены бота = номер раунда

    # Добор карты
    card, game['bot_deck'] = draw_card(game['bot_deck'])
    if card:
        game['bot_hand'].append(card)
    else:
        game = apply_deck_exhaustion_damage(game, 'bot')

    # --- Разыгрывание карт ---
    sorted_hand = sorted(
        [(i, c) for i, c in enumerate(game['bot_hand'])],
        key=lambda x: x[1].get('cost', 0),
        reverse=True
    )

    for _, card_data in sorted_hand:
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
                game['log'].append(
                    f"🤖 Противник разыграл {card_data.get('emoji', '🃏')} "
                    f"{card_data.get('name', '')} (слот {slot + 1})"
                )
                break

    # --- Перемещение существ в экотон ---
    for slot in range(MAX_BACK_ROW):
        if slot == PLANET_SLOT:
            continue
        creature = game['bot_field']['back'][slot]
        if creature and not creature.get('is_planet'):
            move_cost = creature.get('move_cost', 1)
            if bot_atp >= move_cost:
                for eco_slot in range(MAX_LBS):
                    if game['ecotone'][eco_slot] is None:
                        game['ecotone'][eco_slot] = {
                            'owner': 'bot',
                            'card': creature
                        }
                        game['bot_field']['back'][slot] = None
                        bot_atp -= move_cost
                        game['log'].append(
                            f"🤖 Противник переместил "
                            f"{creature.get('emoji', '🃏')} {creature.get('name', '')} "
                            f"в экотон"
                        )
                        break

    # --- Атака ---
    # Приоритет: сначала атакуем существами из экотона, потом из МО
    attacked = False

    # 1. Атака существами из экотона → МО игрока
    for eco_slot in range(MAX_LBS):
        if attacked:
            break
        slot_data = game['ecotone'][eco_slot]
        if slot_data and slot_data['owner'] == 'bot':
            creature = slot_data['card']
            is_ranged = 'Дистанционная атака' in creature.get('keywords', '')

            # Выбираем лучшую цель в МО игрока
            player_back = game['player_field']['back']

            # Проверяем охрану
            guard_slot = _find_guard(player_back)

            if guard_slot is not None:
                # Атакуем охраняющее существо
                game = perform_attack(
                    game, 'ecotone', eco_slot, 'mo', guard_slot
                )
                attacked = True
            else:
                # Атакуем планету
                game = perform_attack(
                    game, 'ecotone', eco_slot, 'mo', PLANET_SLOT
                )
                attacked = True

    # 2. Атака существами из МО → экотон (если есть цели)
    if not attacked:
        for slot in range(MAX_BACK_ROW):
            if attacked:
                break
            if slot == PLANET_SLOT:
                continue
            creature = game['bot_field']['back'][slot]
            if creature and not creature.get('is_planet'):
                is_ranged = 'Дистанционная атака' in creature.get('keywords', '')

                # Ищем цель в экотоне (существо игрока)
                for eco_slot in range(MAX_LBS):
                    eco_data = game['ecotone'][eco_slot]
                    if eco_data and eco_data['owner'] == 'player':
                        game = perform_attack(
                            game, 'mo', slot, 'ecotone', eco_slot
                        )
                        attacked = True
                        break

    # 3. Если не атаковали и есть дистанционные — атакуем МО игрока из МО
    if not attacked:
        for slot in range(MAX_BACK_ROW):
            if attacked:
                break
            if slot == PLANET_SLOT:
                continue
            creature = game['bot_field']['back'][slot]
            if creature and not creature.get('is_planet'):
                is_ranged = 'Дистанционная атака' in creature.get('keywords', '')
                if is_ranged:
                    player_back = game['player_field']['back']
                    guard_slot = _find_guard(player_back)
                    if guard_slot is not None:
                        game = perform_attack(
                            game, 'mo', slot, 'mo', guard_slot
                        )
                    else:
                        game = perform_attack(
                            game, 'mo', slot, 'mo', PLANET_SLOT
                        )
                    attacked = True

    # Проверка завершения игры
    game = check_game_over(game)

    return game


def place_card_on_field(game: Dict[str, Any], card_index: int, slot: int) -> Dict[str, Any]:
    """Размещение карты из руки в указанный слот Места Обитания"""

    if slot == PLANET_SLOT:
        return {'error': '❌ Нельзя разместить карту на слоте планеты!'}

    hand = game.get('player_hand', [])
    if card_index >= len(hand):
        return {'error': '❌ Карта не найдена!'}

    card = hand[card_index]
    cost = card.get('cost', 0)
    current_atp = game.get('current_atp', 0)

    if cost > current_atp:
        return {
            'error': f'❌ Недостаточно мутагенов! Нужно {cost}, есть {current_atp}'
        }

    field = game.get('player_field', {'back': [None] * MAX_BACK_ROW})
    if field['back'][slot] is not None:
        return {'error': '❌ Слот занят!'}

    # Размещаем карту
    field['back'][slot] = card
    game['player_hand'].pop(card_index)
    game['current_atp'] -= cost

    game['log'].append(
        f"🃏 Разыграна {card.get('emoji', '🃏')} {card.get('name', '')} "
        f"в слот {slot + 1}"
    )

    return {'success': True}


def move_to_ecotone(game: Dict[str, Any], slot: int) -> Dict[str, Any]:
    """Перемещение существа из Места Обитания в Экотон"""

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
        game['log'].append(
            f'❌ Недостаточно мутагенов для перемещения! Нужно {move_cost}'
        )
        return game

    # Ищем свободный слот в экотоне
    ecotone = game.get('ecotone', [None] * MAX_LBS)
    for eco_slot in range(MAX_LBS):
        if ecotone[eco_slot] is None:
            ecotone[eco_slot] = {
                'owner': 'player',
                'card': creature
            }
            field['back'][slot] = None
            game['current_atp'] -= move_cost
            game['ecotone'] = ecotone
            game['log'].append(
                f"🚀 {creature.get('emoji', '🃏')} {creature.get('name', '')} "
                f"перемещён в экотон (слот {eco_slot + 1})"
            )
            return game

    game['log'].append('❌ Нет свободных слотов в экотоне!')
    return game


def check_game_over(game: Dict[str, Any]) -> Dict[str, Any]:
    """Проверка завершения игры"""

    if game.get('player_planet_health', STARTING_HP) <= 0:
        game['game_over'] = True
        game['log'].append('😵 Твоя планета уничтожена! Ты проиграл!')

    if game.get('bot_planet_health', STARTING_HP) <= 0:
        game['game_over'] = True
        game['log'].append('🏆 Планета противника уничтожена! Ты победил!')

    return game


def apply_deck_exhaustion_damage(game: Dict[str, Any], target: str) -> Dict[str, Any]:
    """Нанесение урона от истощения колоды по арифметической прогрессии.
    Если колода игрока пуста — его планета получает урон 1, 2, 3...
    """

    if target == 'player':
        if not game['player_deck']:
            game['player_deck_empty_rounds'] = game.get('player_deck_empty_rounds', 0) + 1
            damage = game['player_deck_empty_rounds']
            game['player_planet_health'] = max(0, game['player_planet_health'] - damage)
            game['log'].append(f'💀 Твоя колода пуста! Планета получает {damage} урона')
    elif target == 'bot':
        if not game['bot_deck']:
            game['bot_deck_empty_rounds'] = game.get('bot_deck_empty_rounds', 0) + 1
            damage = game['bot_deck_empty_rounds']
            game['bot_planet_health'] = max(0, game['bot_planet_health'] - damage)
            game['log'].append(
                f'💀 Колода противника пуста! Его планета получает {damage} урона'
            )

    return game