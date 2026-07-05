def start_player_turn(game: Dict[str, Any]) -> Dict[str, Any]:
    """Подготовка хода игрока: добор карты и получение АТФ"""
    
    is_first = game.get('is_first_turn_of_game', False)
    player_goes_first = game.get('player_goes_first', True)
    
    # Если это первый ход игры и игрок ходит первым — не добираем карту
    if not (is_first and player_goes_first):
        old_hand_size = len(game['player_hand'])
        game['player_deck'], game['player_hand'], discarded = draw_card_with_limit(
            game['player_deck'], game['player_hand'], 'игрок'
        )
        if discarded:
            game['log'].append(f"💥 Рука полна! {discarded['emoji']} {discarded['name']} сброшена")
        elif len(game['player_hand']) > old_hand_size:
            # Карта успешно добавлена в руку
            card = game['player_hand'][-1]
            game['log'].append(f"🃏 Ты добрал карту: {card['emoji']} {card['name']}")
    
    # Даём АТФ = номер раунда
    game['current_atp'] = game['round_number']
    game['is_player_turn'] = True
    
    return game