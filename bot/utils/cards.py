# bot/utils/cards.py
import random
from typing import List, Dict, Any, Optional, Tuple

CARDS_DATA = [
    # Animalia (символ 🐾)
    {'name': 'Волк', 'kingdom': 'Animalia', 'rarity': 'Common', 'cost': 1, 'move_cost': 1, 'attack': 2, 'health': 2, 'armor': 0, 'keywords': '', 'emoji': '🐺', 'description': 'Хищник, наносящий средний урон'},
    {'name': 'Змея', 'kingdom': 'Animalia', 'rarity': 'Common', 'cost': 1, 'move_cost': 1, 'attack': 2, 'health': 1, 'armor': 0, 'keywords': '', 'emoji': '🐍', 'description': 'Быстрая атака, но слабая защита'},
    {'name': 'Орёл', 'kingdom': 'Animalia', 'rarity': 'Common', 'cost': 2, 'move_cost': 1, 'attack': 3, 'health': 2, 'armor': 0, 'keywords': 'Дистанционная атака', 'emoji': '🦅', 'description': 'Атакует с воздуха, игнорируя охрану'},
    {'name': 'Паук', 'kingdom': 'Animalia', 'rarity': 'Common', 'cost': 2, 'move_cost': 1, 'attack': 2, 'health': 2, 'armor': 0, 'keywords': '', 'emoji': '🕷️', 'description': 'Универсальный боец'},
    {'name': 'Тигр', 'kingdom': 'Animalia', 'rarity': 'Rare', 'cost': 3, 'move_cost': 1, 'attack': 4, 'health': 3, 'armor': 0, 'keywords': '', 'emoji': '🐯', 'description': 'Мощный хищник с высокой атакой'},
    {'name': 'Медведь', 'kingdom': 'Animalia', 'rarity': 'Rare', 'cost': 3, 'move_cost': 1, 'attack': 3, 'health': 4, 'armor': 1, 'keywords': '', 'emoji': '🐻', 'description': 'Крепкий зверь с бронёй'},

    # Plantae (символ 🌿)
    {'name': 'Кактус', 'kingdom': 'Plantae', 'rarity': 'Common', 'cost': 1, 'move_cost': 1, 'attack': 1, 'health': 3, 'armor': 1, 'keywords': '', 'emoji': '🌵', 'description': 'Колючая защита'},
    {'name': 'Одуванчик', 'kingdom': 'Plantae', 'rarity': 'Common', 'cost': 1, 'move_cost': 1, 'attack': 1, 'health': 1, 'armor': 0, 'keywords': 'Дистанционная атака', 'emoji': '🌼', 'description': 'Атакует спорами издалека'},
    {'name': 'Крапива', 'kingdom': 'Plantae', 'rarity': 'Common', 'cost': 2, 'move_cost': 1, 'attack': 2, 'health': 2, 'armor': 0, 'keywords': '', 'emoji': '🌿', 'description': 'Жгучая защита'},
    {'name': 'Лиана', 'kingdom': 'Plantae', 'rarity': 'Common', 'cost': 2, 'move_cost': 1, 'attack': 2, 'health': 3, 'armor': 0, 'keywords': '', 'emoji': '🌱', 'description': 'Цепкое растение'},
    {'name': 'Дуб', 'kingdom': 'Plantae', 'rarity': 'Rare', 'cost': 3, 'move_cost': 1, 'attack': 2, 'health': 5, 'armor': 2, 'keywords': 'Охрана', 'emoji': '🌳', 'description': 'Могучий страж, защищает соседей'},
    {'name': 'Венерина мухоловка', 'kingdom': 'Plantae', 'rarity': 'Rare', 'cost': 3, 'move_cost': 1, 'attack': 4, 'health': 3, 'armor': 0, 'keywords': 'Дистанционная атака', 'emoji': '🪴', 'description': 'Хищное растение с дистанционной атакой'},

    # Fungi (символ 🍄)
    {'name': 'Плесень', 'kingdom': 'Fungi', 'rarity': 'Common', 'cost': 1, 'move_cost': 1, 'attack': 1, 'health': 2, 'armor': 0, 'keywords': '', 'emoji': '🦠', 'description': 'Живучий грибок'},
    {'name': 'Трутовик', 'kingdom': 'Fungi', 'rarity': 'Common', 'cost': 1, 'move_cost': 1, 'attack': 1, 'health': 3, 'armor': 1, 'keywords': '', 'emoji': '🍄', 'description': 'Крепкий гриб с бронёй'},
    {'name': 'Мухомор', 'kingdom': 'Fungi', 'rarity': 'Common', 'cost': 2, 'move_cost': 1, 'attack': 2, 'health': 2, 'armor': 0, 'keywords': '', 'emoji': '🍄', 'description': 'Ядовитый гриб'},
    {'name': 'Дрожжи', 'kingdom': 'Fungi', 'rarity': 'Common', 'cost': 2, 'move_cost': 1, 'attack': 1, 'health': 3, 'armor': 0, 'keywords': '', 'emoji': '🧫', 'description': 'Быстро размножается'},
    {'name': 'Кордицепс', 'kingdom': 'Fungi', 'rarity': 'Rare', 'cost': 3, 'move_cost': 1, 'attack': 3, 'health': 4, 'armor': 0, 'keywords': '', 'emoji': '🐛', 'description': 'Гриб-паразит, захватывающий разум'},
    {'name': 'Мицелий', 'kingdom': 'Fungi', 'rarity': 'Rare', 'cost': 3, 'move_cost': 1, 'attack': 2, 'health': 4, 'armor': 1, 'keywords': '', 'emoji': '🌲', 'description': 'Разветвлённая сеть грибницы'},

    # Bacteria (символ 🦠)
    {'name': 'Кокк', 'kingdom': 'Bacteria', 'rarity': 'Common', 'cost': 1, 'move_cost': 1, 'attack': 1, 'health': 2, 'armor': 0, 'keywords': '', 'emoji': '🔵', 'description': 'Круглая бактерия'},
    {'name': 'Бацилла', 'kingdom': 'Bacteria', 'rarity': 'Common', 'cost': 1, 'move_cost': 1, 'attack': 2, 'health': 1, 'armor': 0, 'keywords': '', 'emoji': '🟢', 'description': 'Палочковидная бактерия'},
    {'name': 'Спирилла', 'kingdom': 'Bacteria', 'rarity': 'Common', 'cost': 2, 'move_cost': 1, 'attack': 2, 'health': 2, 'armor': 0, 'keywords': 'Дистанционная атака', 'emoji': '🌀', 'description': 'Спиральная бактерия с дистанционной атакой'},
    {'name': 'Цианобактерия', 'kingdom': 'Bacteria', 'rarity': 'Common', 'cost': 2, 'move_cost': 1, 'attack': 2, 'health': 3, 'armor': 0, 'keywords': '', 'emoji': '🟣', 'description': 'Фотосинтезирующая бактерия'},
    {'name': 'Стафилококк', 'kingdom': 'Bacteria', 'rarity': 'Rare', 'cost': 3, 'move_cost': 1, 'attack': 4, 'health': 3, 'armor': 0, 'keywords': '', 'emoji': '🟡', 'description': 'Опасная бактерия с высокой атакой'},
    {'name': 'Стрептомицет', 'kingdom': 'Bacteria', 'rarity': 'Rare', 'cost': 3, 'move_cost': 1, 'attack': 3, 'health': 4, 'armor': 1, 'keywords': '', 'emoji': '🧪', 'description': 'Бактерия, производящая антибиотики'},
]


def create_deck(kingdom: str) -> List[Dict[str, Any]]:
    """Создание колоды для указанного царства"""
    deck = []
    for card_template in CARDS_DATA:
        if card_template['kingdom'] == kingdom:
            for _ in range(2):
                deck.append(dict(card_template))
    return deck


def shuffle_deck(deck: List[Dict[str, Any]]) -> None:
    """Перемешивание колоды"""
    random.shuffle(deck)


def draw_card(deck: List[Dict[str, Any]]) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
    """Взятие карты из колоды"""
    if not deck:
        return None, deck
    card = deck.pop(0)
    return card, deck