# bot/utils/game_logic.py
import random
import copy
from typing import Dict, Any, List, Optional
from bot.config import (
    STARTING_HP, MAX_CARDS_IN_DECK, MAX_HAND_SIZE,
    MAX_BACK_ROW, MAX_LBS, PLANET_SLOT
)
from bot.utils.cards import create_deck, shuffle_deck, draw_card


def create_empty_field() -> Dict[str, List]:
    """Создание пустого поля"""
    return {
        'back': [None] * MAX_BACK_ROW,
        'lbs': [None] * MAX_LBS,
    }


def init_game(player_kingdom: str) -> Dict[str, Any]:
    """Инициализация новой игры"""
    
    # Создаём колоды
    player_deck = create_deck(player_kingdom)
    shuffle_deck(player_deck)
    
    bot_kingdom = random.choice(['Animalia', 'Plantae', 'Fungi', 'Bacteria'])
    bot_deck = create_deck(bot_kingdom)
    shuffle_deck(bot_deck)
    
    # Случайный выбор первого ходящего
    player_goes_first = random.choice([True, False])
    
    # Первый игрок получает 3 карты, второй — 4
    first_hand_size = 3
    second_hand_size = 4
    
    if player_goes_first:
        player_hand = []
        for _ in range(first_hand_size):
            card, player_deck = draw_card(player_deck)
            if card:
                player_hand.append(card)
        
        bot_hand = []
        for _ in range(second_hand_size):
            card, bot_deck = draw_card(bot_deck)
            if card:
                bot_hand.append(card)
    else:
        player_hand = []
        for _ in range(second_hand_size):
            card, player_deck = draw_card(player_deck)
            if card:
                player_hand.append(card)
        
        bot_hand = []
        for _ in range(first_hand_size):
            card, bot_deck = draw_card(bot_deck)
            if card:
                bot_hand.append(card)
    
    # Создаём поле с планетой в слоте 3
    player_field = create_empty_field()
    player_field['back'][PLANET_SLOT - 1] = {'is_planet': True, 'health': STARTING_HP}
    
    bot_field = create_empty_field()
    bot_field['back'][PLANET_SLOT - 1] = {'is_planet': True, 'health': STARTING_HP}
    
    first_turn_text = "Твой ход!" if player_goes_first else "Противник ходит первым..."
    
    return {
        'player_kingdom': player_kingdom,
        'bot_kingdom': bot_kingdom,
        'player_deck': player_deck,
        'bot_deck': bot_deck,
        'player_hand': player_hand,
        'bot_hand': bot_hand,
        'player_field': player_field,
        'bot_field': bot_field,
        'player_planet_health': STARTING_HP,
        'bot_planet_health': STARTING_HP,
        'round_number': 1,
        'current_atp': 1,
        'is_player_turn': player_goes_first,
        'is_first_turn_of_game': True,
        'bot_moved_this_round': False,
        'game_over': False,
        'log': ['🧬 Игра начата!', first_turn_text],
    }


def start_player_turn(game: Dict[str, Any]) -> Dict[str, Any]:
    """Подготовка хода игрока: добор карты и получение АТФ"""
    
    is_first = game.get('is_first_turn_of_game', False)
    player_goes_first = game.get('player_goes_first', True)
    
    # Если это первый ход игры и игрок ходит первым — не добираем карту
    if not (is_first and player_goes_first):
        if game['player_deck']:
            card, game['player_deck'] = draw_card(game['player_deck'])
            if card:
                game['player_hand'].append(card)
                game['log'].append(f"🃏 Ты добрал карту: {card['emoji']} {card['name']}")
    
    # Даём АТФ = номер раунда
    game['current_atp'] = game['round_number']
    game['is_player_turn'] = True
    
    return game


def get_planet_slot(field: Dict) -> int:
    """Получение слота, где находится планета"""
    for i, slot in enumerate(field['back']):
        if slot and slot.get('is_planet'):
            return i
    return PLANET_SLOT - 1


def place_card_on_field(
    game: Dict[str, Any], 
    card_index: int, 
    slot: int
) -> Dict[str, Any]:
    """Постановка карты на поле (автоматическое смещение планеты)"""
    
    if card_index >= len(game['player_hand']):
        return game
    
    card = game['player_hand'].pop(card_index)
    
    # Проверка АТФ
    if game['current_atp'] < card.get('cost', 1):
        game['player_hand'].insert(card_index, card)
        return game
    
    # Проверка слота
    if slot >= MAX_BACK_ROW:
        game['player_hand'].insert(card_index, card)
        return game
    
    # Проверка, не занят ли слот планетой
    if game['player_field']['back'][slot] and game['player_field']['back'][slot].get('is_planet'):
        # Планета смещается вправо
        planet_slot = get_planet_slot(game['player_field'])
        if planet_slot == MAX_BACK_ROW - 1:
            game['player_hand'].insert(card_index, card)
            return game
        # Перемещаем планету вправо
        for i in range(planet_slot + 1, MAX_BACK_ROW):
            if game['player_field']['back'][i] is None:
                game['player_field']['back'][i] = game['player_field']['back'][planet_slot]
                game['player_field']['back'][planet_slot] = None
                break
    
    # Проверка свободного слота
    if game['player_field']['back'][slot] is not None:
        # Сдвиг существ влево
        for i in range(slot, 0, -1):
            if game['player_field']['back'][i-1] is None:
                game['player_field']['back'][i-1] = game['player_field']['back'][i]
                game['player_field']['back'][i] = None
                break
    
    # Ставим карту
    if game['player_field']['back'][slot] is None:
        game['player_field']['back'][slot] = card
        game['current_atp'] -= card.get('cost', 1)
        game['log'].append(f"✅ Ты поставил {card['emoji']} {card['name']} в слот {slot+1}")
    else:
        game['player_hand'].insert(card_index, card)
    
    return game


def move_to_ecotone(game: Dict[str, Any], slot: int) -> Dict[str, Any]:
    """Перемещение существа из МО в экотон"""
    
    if game['current_atp'] < 1:
        return game
    
    if slot >= MAX_BACK_ROW:
        return game
    
    card = game['player_field']['back'][slot]
    if not card or card.get('is_planet'):
        return game
    
    # Проверяем, есть ли свободный слот в экотоне
    free_slot = None
    for i, s in enumerate(game['player_field']['lbs']):
        if s is None:
            free_slot = i
            break
    
    if free_slot is None:
        return game
    
    game['player_field']['back'][slot] = None
    game['player_field']['lbs'][free_slot] = card
    game['current_atp'] -= 1
    game['log'].append(f"🚀 {card['emoji']} {card['name']} перешёл в экотон")
    
    return game


def perform_attack(
    game: Dict[str, Any],
    attacker_slot: int,
    target_type: str,
    target_slot: int = None
) -> Dict[str, Any]:
    """Выполнение атаки"""
    
    # Находим атакующего
    attacker = game['player_field']['lbs'][attacker_slot]
    if not attacker:
        return game
    
    if game['current_atp'] < 1:
        return game
    
    # Проверка дистанционной атаки
    is_ranged = 'Дистанционная атака' in attacker.get('keywords', '')
    if not is_ranged and not game['player_field']['lbs'][attacker_slot]:
        return game
    
    # Выбор цели
    if target_type == 'planet':
        damage = max(0, attacker.get('attack', 0))
        game['bot_planet_health'] = max(0, game['bot_planet_health'] - damage)
        game['log'].append(f"⚔️ {attacker['emoji']} {attacker['name']} атакует планету! -{damage} HP")
        
    elif target_type == 'creature' and target_slot is not None:
        # Проверяем охрану
        if is_protected(game['bot_field'], target_slot):
            game['log'].append("🛡️ Цель защищена охраной!")
            return game
        
        target = game['bot_field']['back'][target_slot]
        if not target or target.get('is_planet'):
            return game
        
        damage = max(0, attacker.get('attack', 0) - target.get('armor', 0))
        target['health'] = target.get('health', 0) - damage
        game['log'].append(f"⚔️ {attacker['emoji']} {attacker['name']} атакует {target['emoji']} {target['name']}! -{damage} HP")
        
        if target['health'] <= 0:
            game['bot_field']['back'][target_slot] = None
            game['log'].append(f"💀 {target['emoji']} {target['name']} уничтожен!")
    
    game['current_atp'] -= 1
    return game


def is_protected(field: Dict, slot: int) -> bool:
    """Проверка, защищена ли цель охраной"""
    # Проверяем соседние слоты
    for i in [slot - 1, slot + 1]:
        if 0 <= i < MAX_BACK_ROW:
            card = field['back'][i]
            if card and 'Охрана' in card.get('keywords', ''):
                return True
    return False


def bot_turn(game: Dict[str, Any]) -> Dict[str, Any]:
    """Ход бота"""
    
    is_first = game.get('is_first_turn_of_game', False)
    bot_goes_first = not game.get('is_player_turn', True)
    
    game['log'].append("🤖 Ход противника...")
    
    # Если это первый ход игры и бот ходит первым — не добираем карту
    if not (is_first and bot_goes_first):
        if game['bot_deck']:
            card, game['bot_deck'] = draw_card(game['bot_deck'])
            if card:
                game['bot_hand'].append(card)
    
    # Даём боту АТФ = номер раунда
    game['current_atp'] = game['round_number']
    
    # Постановка карты
    placed = False
    for i, card in enumerate(game['bot_hand']):
        if game['current_atp'] >= card.get('cost', 1):
            for slot in range(MAX_BACK_ROW):
                if game['bot_field']['back'][slot] is None:
                    game['bot_hand'].pop(i)
                    game['bot_field']['back'][slot] = card
                    game['current_atp'] -= card.get('cost', 1)
                    placed = True
                    game['log'].append(f"🤖 Противник поставил {card['emoji']} {card['name']}")
                    break
            if placed:
                break
    
    # Атака
    for i, card in enumerate(game['bot_field']['lbs']):
        if card and game['current_atp'] >= 1:
            # Атакуем планету
            damage = max(0, card.get('attack', 0))
            game['player_planet_health'] = max(0, game['player_planet_health'] - damage)
            game['log'].append(f"🤖 {card['emoji']} {card['name']} атакует планету! -{damage} HP")
            game['current_atp'] -= 1
            break
    
    # Если это был первый ход — снимаем флаг
    if is_first:
        game['is_first_turn_of_game'] = False
    
    # Проверка окончания
    if game['player_planet_health'] <= 0:
        game['game_over'] = True
        game['log'].append("💀 Ты проиграл! Планета уничтожена.")
    
    if game['bot_planet_health'] <= 0:
        game['game_over'] = True
        game['log'].append("🏆 Ты победил! Планета противника уничтожена.")
    
    return game


def check_game_over(game: Dict[str, Any]) -> bool:
    """Проверка окончания игры"""
    if game['player_planet_health'] <= 0:
        game['game_over'] = True
        game['log'].append("💀 Ты проиграл! Планета уничтожена.")
        return True
    
    if game['bot_planet_health'] <= 0:
        game['game_over'] = True
        game['log'].append("🏆 Ты победил! Планета противника уничтожена.")
        return True
    
    return False