class Player:
    """A class of a citizen player.

    Args:
        name (str): The name of the player in the Telegram.
        userid (int): The userid of the player in the Telegram.

    Attributes:
        name (str): The name of the player in the Telegram.
        _is_alive (bool): If the player is still alive.
        _role (str): The role of the player in the game.
        userid (int): The userid of the player in the Telegram.
        _voted (bool): If the player had already voted in this turn.
    """
    def __init__(self, name: str, userid: int):
        self.name: str = name
        self._is_alive: bool = True
        self._role: str = 'citizen'
        self.userid: int = userid
        self._voted: bool = False
        self._emoji: str = '\U0001F477'

    def __str__(self):
        return f'{self.name}, {self._role} {self._emoji}'


class Murderer(Player):
    def __init__(self, name: str, userid: int):
        super().__init__(name, userid)
        self._role: str = 'murderer'
        self._detained: bool = False
        self._emoji: str = '\U0001F9DB'

    @staticmethod
    def kill(player: Player) -> None:
        """Kill a player."""
        player._is_alive = False


class Policeman(Player):
    def __init__(self, name: str, userid: int):
        super().__init__(name, userid)
        self._role: str = 'policeman'
        self._emoji: str = '\U0001F46E'

    @staticmethod
    def detain(player: Player) -> bool:
        """Check if the detained player is the murderer."""
        if isinstance(player, Murderer):
            player._detained = True
            return True
        return False
