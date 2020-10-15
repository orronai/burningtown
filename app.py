import time

from application.bot import bot
from models.game import Game, MIN_PLAYERS
from utils.log import log


GAME = Game()


@bot.message_handler(func=lambda msg: msg.text == '!game')
def start_join_stage(message):
    """Start the game - the join stage."""
    if message.chat.type == 'supergroup' and not GAME._status:
        bot.send_message(message.chat.id, (
            'A burning town game is about to start.\n'
            'In order to join, type: !join\n'
            'In order to see the playing players, type: !players\n'
            'In order to stop the game, type: !stop\n'
            'Players whose this game is their first time,'
            'need to send a private message to me.'
        ))
        GAME.join_stage(message.chat.id)
        join_game(message)


@bot.message_handler(func=lambda msg: msg.text == '!start')
def start_game_stage(message):
    """Start the game - the game stage."""
    if message.chat.type == 'supergroup' and GAME._status == 'join':
        if GAME.check_start():
            bot.send_message(message.chat.id, 'The game has now started!')
            result = GAME.start()
            bot.send_message(
                message.chat.id, f'Game over! Team {result} had won!',
            )
            GAME.reset_game()
        else:
            bot.send_message(message.chat.id, (
                "You don't have enough players.\n"
                'In order to start a game you need at least '
                f'{MIN_PLAYERS} players.'
            ))


@bot.message_handler(func=lambda msg: msg.text == '!stop')
def stop_game(message):
    """Stop the game."""
    if message.chat.type == 'supergroup' and GAME._status:
        GAME.reset_game()
        bot.send_message(message.chat.id, (
            'The game had stopped!\n'
            'In order to start a new game, type !game'
        ))


@bot.message_handler(func=lambda msg: msg.text == '!join')
def join_game(message):
    """Add a player to the game."""
    if message.chat.type == 'supergroup' and GAME._status == 'join':
        name = f'{message.from_user.first_name}'
        if GAME.check_sent_pm(message.from_user.id):
            GAME.add_player(name, message.from_user.id)
        else:
            bot.send_message(message.chat.id, (
                f'{name}, in order to join the game for your first time '
                'please send me a private message.'
            ))


@bot.message_handler(
    func=lambda msg: (
        msg.text is not None
        and msg.chat.type == 'private'
    ),
)
def add_playerid_to_file(message):
    if not GAME.check_sent_pm(message.from_user.id):
        with open('telegram-users.txt', 'a') as file:
            file.write(str(message.from_user.id) + '\n')
            bot.send_message(message.from_user.id, (
                f'{message.from_user.first_name}, you are now registered. '
                "You don't have to register again."
            ))


@bot.message_handler(func=lambda msg: msg.text == '!players')
def the_players(message):
    """Get the playing players."""
    if message.chat.type == 'supergroup' and GAME._status:
        GAME.get_players()


while True:
    try:
        bot.polling()
    except Exception as e:
        log.info(str(e))
        time.sleep(10)
