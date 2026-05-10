import random
from dataclasses import dataclass, field

from log.config import get_sim_logger, setup_logging

from .merchant import Merchant, Shop
from .pirate import Pirate, PirateCrew
from .player import Player
from .villager import Villager

logger = get_sim_logger()

DAY_MAX: int = 10000
DEFAULT_PIRATE_MONEY: int = 0


@dataclass
class Simulation:
    """
    Class representing the simulation of a game.
    """

    players: list[Player]

    day: int = field(init=False, default=0)
    pirate_money: int = field(init=False, default=DEFAULT_PIRATE_MONEY)

    @property
    def pirates(self) -> list[Pirate]:
        """
        Return a list of all the pirates in the simulation.
        """
        return [p for p in self.players if isinstance(p, Pirate) and not p.dead]

    @property
    def villagers(self) -> list[Villager]:
        """
        Return a list of all the villagers in the simulation.
        """
        return [v for v in self.players if isinstance(v, Villager) and not v.dead]

    @property
    def merchants(self) -> list[Merchant]:
        """
        Return a list of all the merchants in the simulation.
        """
        return [m for m in self.players if isinstance(m, Merchant) and not m.dead]

    def __post_init__(self) -> None:
        # Set simulation attribute for each player
        for player in self.players:
            player.simulation = self

        setup_logging(self)

    @property
    def shops(self) -> list[Shop]:
        """
        Return a list of all the items that all the merchants own.
        """
        all_items = []
        for merchant in self.merchants:
            all_items.extend(merchant.store)
        return all_items

    @property
    def pirates_in_expedition(self) -> list[Pirate]:
        """
        Return a list of the pirates who are in expedition.
        """
        return [p for p in self.pirates if p.at_sea]

    def step(self) -> None:
        """
        Advance the simulation by one step.
        """
        self.day += 1

        random.shuffle(self.players)  # So it's not always the same order

        # Each player chooses an action
        for player in self.players:
            player.choose_action()

        # Each player chooses a target
        for player in self.players:
            player.choose_target()

        # Each player advances one step in the simulation
        for player in self.players:
            player.step()

    def run(self):
        """
        Run the simulation until the day limit is reached.
        """
        logger.info("BEGIN")

        while self.day < DAY_MAX:
            self.step()

        logger.info("END")


if __name__ == "__main__":
    crew = PirateCrew(money=500)
    m1 = Merchant(_money=2000)
    for _ in range(3):
        m1.store.append(Shop.from_item(owner=m1))
    m1.store[0].is_food = True
    m1.store[0].owned_quantity = 100

    sim = Simulation(
        [Pirate(crew=crew, food=10), m1, Villager(_money=100, happiness=50)]
    )

    sim.run()
