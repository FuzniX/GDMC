import random
from dataclasses import dataclass, field

from log.config import get_sim_logger, setup_logging

from .merchant import MAX_ITEMS, Merchant, Shop
from .pirate import Pirate
from .player import Player
from .villager import Villager

DAY_MAX: int = 10000
DEFAULT_PIRATE_MONEY: int = 50000

columns = [
    "day",
    "type",
    "id",
    "infection_status",
    "action_choice",
    "target",
    "idle_period",
    "money",
    "happiness",
    "bounty",
    "food",
    "days_at_sea",
    "closure_period",
] + [
    f"{k}{i + 1}"
    for i in range(MAX_ITEMS)
    for k in ["price", "owned_quantity", "max_quantity", "name", "is_food"]
]

logger = get_sim_logger()


@dataclass
class Simulation:
    """
    Class representing the simulation of a game.
    """

    players: list[Player]
    days: int = DAY_MAX

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

        # Log the state of the simulation
        for player in self.players:
            logger.stats(player.log)

    def run(self):
        """
        Run the simulation until the day limit is reached.
        """
        logger.info("BEGIN")

        logger.stats(",".join(columns))
        while self.day < self.days:
            self.step()

        logger.info("END")

    @staticmethod
    def generate(
        nb_villagers: int = 1,
        nb_merchants: int = 1,
        nb_pirates: int = 1,
        days: int = DAY_MAX,
    ) -> "Simulation":
        """
        Creates a simulation with the specified number of villagers, merchants, and pirates.
        """
        players = []

        # Villagers
        for _ in range(nb_villagers):
            v = Villager(
                happiness=random.randint(0, 1000),
                _money=random.randint(0, 10000),
            )
            players.append(v)

        # Merchants
        for _ in range(nb_merchants):
            m = Merchant(_money=random.randint(0, 50000))
            nb_shops = random.randint(1, MAX_ITEMS)
            for _ in range(nb_shops):
                m.store.append(Shop.from_item(owner=m))
            players.append(m)

        # Pirates
        for _ in range(nb_pirates):
            p = Pirate(
                bounty=random.randint(0, 10000),
                food=random.randint(0, 100),
            )
            players.append(p)

        return Simulation(players=players, days=days)


if __name__ == "__main__":
    Simulation.generate(
        nb_villagers=20,
        nb_merchants=20,
        nb_pirates=20,
        days=100,
    ).run()
