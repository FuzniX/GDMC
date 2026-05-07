import random
from dataclasses import dataclass, field

from .merchant import Merchant, Shop
from .pirate import Pirate
from .player import Player
from .villager import Villager

DAY_MAX: int = 10000


@dataclass
class Simulation:
    players: list[Player]

    day: int = field(init=False)

    @property
    def pirates(self) -> list[Pirate]: # return a list of all the pirates
        return [p for p in self.players if isinstance(p, Pirate) and not p.dead]

    @property
    def villagers(self) -> list[Villager]: # return a list of all the villagers
        return [v for v in self.players if isinstance(v, Villager) and not v.dead]

    @property
    def merchants(self) -> list[Merchant]: # return a list of all the merchants
        return [m for m in self.players if isinstance(m, Merchant) and not m.dead]

    def __post_init__(self) -> None:
        # Set simulation attribute for each player
        for player in self.players:
            player.simulation = self

    @property
    def shops(self) -> list[Shop]: # return a list of all the items that all the merchants own
        all_items = []
        for merchant in self.merchants:
            all_items.extend(merchant.store)
        return all_items

    @property
    def pirates_in_expedition(self) -> list[Pirate]: # return a list of the pirates who are in expedition
        return [p for p in self.pirates if p.at_sea]

    def step(self) -> None:
        random.shuffle(self.players)  # So it's not always the same order

        for player in self.players: # each player choose an action
            player.choose_action()

        for player in self.players: # each player interract with a random target depending on the player and the type of action
            player.choose_target()

        for player in self.players: # each player advance one step in the simulation
            player.step()

        self.day += 1

    def run(self):
        while self.day < DAY_MAX:
            self.step()


if __name__ == "__main__":
    simulation = Simulation([])
    # simulation.run()
