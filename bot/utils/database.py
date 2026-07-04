# bot/utils/database.py
import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from bot.config import DATABASE_PATH
def get_db_connection():
    """Получение соединения с базой данных"""
    Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn
def init_database():
    """Инициализация базы данных"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Таблица карт
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            kingdom TEXT NOT NULL,
            rarity TEXT NOT NULL,
            cost INTEGER DEFAULT 1,
            attack INTEGER DEFAULT 0,
            health INTEGER DEFAULT 0,
            armor INTEGER DEFAULT 0,
            keywords TEXT DEFAULT '',
            emoji TEXT DEFAULT '🃏',
            description TEXT DEFAULT ''
        )
    ''')
    
    # Таблица игр
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            player_kingdom TEXT NOT NULL,
            bot_kingdom TEXT NOT NULL,
            player_deck TEXT NOT NULL,
            bot_deck TEXT NOT NULL,
            player_hand TEXT NOT NULL,
            bot_hand TEXT NOT NULL,
            player_field TEXT NOT NULL,
            bot_field TEXT NOT NULL,
            player_planet_health INTEGER DEFAULT 10,
            bot_planet_health INTEGER DEFAULT 10,
            round_number INTEGER DEFAULT 1,
            current_atp INTEGER DEFAULT 1,
            is_player_turn INTEGER DEFAULT 1,
            game_over INTEGER DEFAULT 0,
            log TEXT DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
def save_game(user_id: int, game_state: Dict[str, Any]):
    """Сохранение игры"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM games WHERE user_id = ? AND game_over = 0', (user_id,))
    existing = cursor.fetchone()
    
    if existing:
        cursor.execute('''
            UPDATE games SET
                player_kingdom = ?, bot_kingdom = ?,
                player_deck = ?, bot_deck = ?,
                player_hand = ?, bot_hand = ?,
                player_field = ?, bot_field = ?,
                player_planet_health = ?, bot_planet_health = ?,
                round_number = ?, current_atp = ?,
                is_player_turn = ?, game_over = ?, log = ?
            WHERE user_id = ? AND game_over = 0
        ''', (
            game_state['player_kingdom'],
            game_state['bot_kingdom'],
            json.dumps(game_state['player_deck']),
            json.dumps(game_state['bot_deck']),
            json.dumps(game_state['player_hand']),
            json.dumps(game_state['bot_hand']),
            json.dumps(game_state['player_field']),
            json.dumps(game_state['bot_field']),
            game_state['player_planet_health'],
            game_state['bot_planet_health'],
            game_state['round_number'],
            game_state['current_atp'],
            1 if game_state['is_player_turn'] else 0,
            1 if game_state['game_over'] else 0,
            json.dumps(game_state.get('log', [])),
            user_id
        ))
    else:
        cursor.execute('''
            INSERT INTO games (
                user_id, player_kingdom, bot_kingdom,
                player_deck, bot_deck, player_hand, bot_hand,
                player_field, bot_field,
                player_planet_health, bot_planet_health,
                round_number, current_atp, is_player_turn, game_over, log
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            game_state['player_kingdom'],
            game_state['bot_kingdom'],
            json.dumps(game_state['player_deck']),
            json.dumps(game_state['bot_deck']),
            json.dumps(game_state['player_hand']),
            json.dumps(game_state['bot_hand']),
            json.dumps(game_state['player_field']),
            json.dumps(game_state['bot_field']),
            game_state['player_planet_health'],
            game_state['bot_planet_health'],
            game_state['round_number'],
            game_state['current_atp'],
            1 if game_state['is_player_turn'] else 0,
            1 if game_state['game_over'] else 0,
            json.dumps(game_state.get('log', []))
        ))
    
    conn.commit()
    conn.close()
def load_game(user_id: int) -> Optional[Dict[str, Any]]:
    """Загрузка игры"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM games WHERE user_id = ? AND game_over = 0', (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    row = dict(row)
    return {
        'player_kingdom': row['player_kingdom'],
        'bot_kingdom': row['bot_kingdom'],
        'player_deck': json.loads(row['player_deck']),
        'bot_deck': json.loads(row['bot_deck']),
        'player_hand': json.loads(row['player_hand']),
        'bot_hand': json.loads(row['bot_hand']),
        'player_field': json.loads(row['player_field']),
        'bot_field': json.loads(row['bot_field']),
        'player_planet_health': row['player_planet_health'],
        'bot_planet_health': row['bot_planet_health'],
        'round_number': row['round_number'],
        'current_atp': row['current_atp'],
        'is_player_turn': bool(row['is_player_turn']),
        'game_over': bool(row['game_over']),
        'log': json.loads(row['log']),
    }
def delete_game(user_id: int):
    """Удаление игры"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM games WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def seed_cards():
    """Заполнение таблицы карт начальными данными (заглушка)"""
    # Карты уже определены в cards.py, функция для будущего расширения
    pass