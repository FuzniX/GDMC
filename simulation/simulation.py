from dataclasses import dataclass

from player import Player


@dataclass
class Simulation:
    players: list[Player]
    day: int = 0