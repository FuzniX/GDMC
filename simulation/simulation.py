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
    def pirates(self) -> list[Pirate]:
        return [p for p in self.players if isinstance(p, Pirate) and not p.dead]

    @property
    def villagers(self) -> list[Villager]:
        return [v for v in self.players if isinstance(v, Villager) and not v.dead]

    @property
    def merchants(self) -> list[Merchant]:
        return [m for m in self.players if isinstance(m, Merchant) and not m.dead]

    def __post_init__(self) -> None:
        # Set simulation attribute for each player
        for player in self.players:
            player.simulation = self

    @property
    def shops(self) -> list[Shop]:
        all_items = []
        for merchant in self.merchants:
            all_items.extend(merchant.store)
        return all_items

    @property
    def pirates_in_expedition(self) -> list[Pirate]:
        return [p for p in self.pirates if p.at_sea]

    def step(self) -> None:
        random.shuffle(self.players)  # So it's not always the same order

        for player in self.players:
            player.choose_action()

        for player in self.players:
            player.choose_target()

        for player in self.players:
            player.step()

        self.day += 1

    def run(self):
        while self.day < DAY_MAX:
            self.step()


if __name__ == "__main__":
    simulation = Simulation([])
    # simulation.run()
