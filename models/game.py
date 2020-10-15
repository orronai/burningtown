from collections import defaultdict
import random
from pathlib import Path
import time
from typing import DefaultDict, List, Optional, Union

from application.bot import bot
from models.players import Murderer, Player, Policeman


PROJECT_DIR = Path(__file__).resolve().parent.parent
MIN_PLAYERS = 4


class Game:
    """A class of the burning town game.

    Attributes:
        _players (list): A list of the playing Players.
        _mafia (Murderer): An instance of the mafia player.
        _policeman (Policeman): An instance of the policeman player.
        _status (str): The status of the game: ('join', 'game').
        _group_chat_id (int): The id of the group chat in the Telegram.
        _votes (defaultdict(int)): A dictionary of the votes.
        _finished_stage (bool): An indicator whether a stage has finished.
        _current_turn (Player): Which player turn is that.
    """
    def __init__(self):
        self._players: List[Player] = []
        self._mafia: Murderer = None
        self._policeman: Policeman = None
        self._status: Optional[str] = None
        self._group_chat_id: int = None
        self._votes: DefaultDict[Player, int] = defaultdict(int)
        self._finished_stage: bool = False
        self._current_turn: Optional[Player] = None

    def reset_game(self) -> None:
        """Reset the game."""
        self._players = []
        self._status = None
        self._mafia = None
        self._policeman = None
        self._votes = defaultdict(int)

    def _reset_votes(self) -> None:
        """Reset the votes results."""
        self._votes = defaultdict(int)
        for player in self._players:
            if player._is_alive:
                player._voted = False

    def join_stage(self, group_id: int) -> None:
        """Start the join stage."""
        self._status = 'join'
        self._group_chat_id = group_id

    def add_player(self, player_name: str, user_id: int) -> None:
        """Add a player to the game."""
        if not self.check_if_player_exists(player_name):
            self._players.append(Player(player_name, user_id))

    def check_if_player_exists(self, player_name) -> Union[Player, bool]:
        """Check if the player name is playing and is alive."""
        for player in self._players:
            if player.name == player_name and player._is_alive:
                return player
        return False

    @staticmethod
    def check_sent_pm(author_id: int) -> bool:
        """Check if the player is in the bot's list of players."""
        if not (PROJECT_DIR / 'telegram-users.txt').is_file():
            return False
        with open('telegram-users.txt', 'r') as file:
            return str(author_id) in file.read().splitlines()

    def num_of_players_alive(self) -> int:
        """Return how many alive players left."""
        return sum(map(lambda player: player._is_alive, self._players))

    def get_players(self) -> None:
        """Send a message in Telegram of the playing players."""
        players = ', '.join(
            player.name for player in self._players if player._is_alive
        ).strip()
        bot.send_message(self._group_chat_id, f'Playing players:\n{players}')

    def check_win(self) -> Union[str, bool]:
        """Check if the game is over - if there is a winning team."""
        if not self._mafia._is_alive or self._mafia._detained:
            return 'citizens'
        if self.num_of_players_alive() <= 2:
            return 'mafia'
        return False

    def _create_players(self) -> None:
        """Create the players and send messages to the players."""
        murderer_index, policeman_index = random.sample(
            range(len(self._players)), k=2,
        )
        self._mafia = self._players[murderer_index] = Murderer(
            self._players[murderer_index].name,
            self._players[murderer_index].userid,
        )
        self._policeman = self._players[policeman_index] = Policeman(
            self._players[policeman_index].name,
            self._players[policeman_index].userid,
        )
        for player in self._players:
            bot.send_message(player.userid, f'Your role: {player._role}')

    def vote(self, player: Player, author_id: int) -> None:
        """Vote to kill a player."""
        self._votes[player] += 1
        for player in self._players:
            if player.userid == author_id:
                player._voted = True

    def _check_user_voted(self, author_id: int) -> bool:
        """Check if the user who voted is alive and not already voted."""
        for player in self._players:
            if (
                player.userid == author_id
                and player._is_alive and not player._voted
            ):
                return True
        return False

    def check_votes_and_kill(self) -> bool:
        """Kill the player with the most votes."""
        votes_items = sorted(
            self._votes.items(), key=lambda item: item[-1], reverse=True,
        )
        if len(votes_items) > 1:
            if votes_items[0][-1] == votes_items[1][-1]:
                bot.send_message(
                    self._group_chat_id, 'There is a draw. No one had died',
                )
                return False
        votes_items[0][0]._is_alive = False
        bot.send_message(
            self._group_chat_id, f'{str(votes_items[0][0])} is now dead',
        )
        return True

    def check_num_of_votes(self) -> bool:
        """Check if a player got most of the votes."""
        if self._votes:
            highest_vote = sorted(
                self._votes.items(), key=lambda item: item[-1], reverse=True,
            )[0]
            if highest_vote[-1] > self.num_of_players_alive() / 2:
                return True
        return False

    def check_start(self) -> bool:
        """Check if there are enough players to start the game."""
        # You can't play with less than MIN_PLAYERS players.
        return len(self._players) >= MIN_PLAYERS

    def start(self) -> Union[str, bool]:
        """Start the game stage."""
        self._status = 'game'
        self._create_players()
        self._current_turn = self._mafia
        while not self.check_win():
            self.get_players()
            self.start_round()
            self._reset_votes()
        return self.check_win()

    def start_round(self) -> None:
        """Start a round."""
        bot.send_message(self._group_chat_id, "It's the mafia turn")
        bot.send_message(
            self._mafia.userid, 'Please send me a player you want to kill',
        )
        # Reset the stage after the policeman turn
        self._finished_stage = False
        self._police_mafia_turn()
        self._finished_stage = False
        if self._policeman._is_alive and self.num_of_players_alive() > 2:
            self._current_turn = self._policeman
            bot.send_message(self._group_chat_id, "It's the policeman turn")
            bot.send_message(
                self._policeman.userid,
                'Please send me which player you suspect him as mafia player',
            )
            self._police_mafia_turn()
            self._current_turn = self._mafia
        if not self._mafia._detained and self.num_of_players_alive() > 2:
            # If the policeman detained the mafia - the game is over
            bot.send_message(self._group_chat_id, (
                'Time to vote!\n'
                'Everyone needs to type here which player he suspect in'
            ))
            self._votes_stage()
            self.check_votes_and_kill()

    def _police_mafia_turn(self) -> None:
        """The policeman and murderer turns."""
        while not self._finished_stage:
            time.sleep(3)

            @bot.message_handler(func=lambda msg: msg.text is not None
                                 and msg.chat.id == self._current_turn.userid
                                 and self._status == 'game')
            def check_turn(message):
                check = self.check_if_player_exists(message.text)
                if not check:
                    bot.send_message(
                        message.chat.id,
                        'Player does not exist, send me another one',
                    )

                    @bot.message_handler(func=lambda msg: msg.text is not None)
                    def check_message(message):
                        check_turn(message)
                else:
                    if self._current_turn == self._mafia:
                        self._mafia.kill(check)
                        bot.send_message(
                            self._group_chat_id, f'{str(check)} is now dead',
                        )
                    else:  # Policeman turn
                        self._policeman.detain(check)
                    self._finished_stage = True
        return

    def _votes_stage(self) -> None:
        """The votes stage."""
        while (
            sum(self._votes.values()) < self.num_of_players_alive()
            and not self.check_num_of_votes()
        ):
            time.sleep(3)

            @bot.message_handler(func=lambda msg: msg.text is not None
                                 and msg.chat.id == self._group_chat_id
                                 and self._status == 'game')
            def check_vote_stage(message):
                if self._check_user_voted(message.from_user.id):
                    existed_vote = self.check_if_player_exists(message.text)
                    if existed_vote:
                        self.vote(existed_vote, message.from_user.id)
                        bot.send_message(
                            message.chat.id,
                            (
                                f'{message.from_user.first_name}'
                                f'voted for {message.text}'
                            ),
                        )
        return
