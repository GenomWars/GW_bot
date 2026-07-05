def apply_deck_exhaustion_damage(game: Dict[str, Any], target: str) -> Dict[str, Any]:
    """Нанесение урона от истощения колоды по арифметической прогрессии.
    Если колода игрока пуста — его планета получает урон 1, 2, 3..."""
    
    if target == 'player':
        # Проверяем колоду игрока — если пуста, урон планете игрока
        if not game['player_deck']:
            game['player_deck_empty_rounds'] = game.get('player_deck_empty_rounds', 0) + 1
            damage = game['player_deck_empty_rounds']
            game['player_planet_health'] = max(0, game['player_planet_health'] - damage)
            game['log'].append(f"💀 Твоя колода пуста! Планета получает {damage} урона")
    elif target == 'bot':
        # Проверяем колоду бота — если пуста, урон планете бота
        if not game['bot_deck']:
            game['bot_deck_empty_rounds'] = game.get('bot_deck_empty_rounds', 0) + 1
            damage = game['bot_deck_empty_rounds']
            game['bot_planet_health'] = max(0, game['bot_planet_health'] - damage)
            game['log'].append(f"💀 Колода противника пуста! Его планета получает {damage} урона")
    
    return game