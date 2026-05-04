from dataclasses import dataclass

from player import Player
from villager import Villager
from pirate import Pirate
from merchant import Merchant


@dataclass
class Simulation:
    players: list[Player]
    day: int = 0
    DAY_MAX : int = 10000


if __name__ == "__main__":
    simulation = Simulation
    day : int = 0
    while day < simulation.DAY_MAX :
        for i in range(len(simulation.players)):
            if simulation.players[i].can_play:
                if isinstance(simulation.players[i], Villager)
            simulation.players[i].interact_with()