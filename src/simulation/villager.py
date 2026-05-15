import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Optional

from log.config import get_sim_logger
from src.generation.houses.house import House
from src.generation.houses.villager_house import VillagerHouse

from .enums import ActionChoice
from .exceptions import ImpossibleActionError, WrongTargetError
from .player import Player

if TYPE_CHECKING:
    from .merchant import Shop
    from .pirate import Pirate

WORK_MONEY = 100
WORK_HAPPINESS = 10

BARTER_FACTOR = 2
HAPPINESS_GAIN_FACTOR = 0.15

DEFAULT_HAPPINESS = 0
DEFAULT_MONEY = 0

logger = get_sim_logger()


@dataclass
class Villager(Player["Pirate | Shop"]):
    """
    Class representing a villager player in the simulation.
    """

    happiness: int = DEFAULT_HAPPINESS
    _money: int = DEFAULT_MONEY

    @property
    def _action_map(self) -> dict[ActionChoice, Callable[[], None]]:
        return super().action_map | {
            ActionChoice.Work: self.work,
            ActionChoice.Barter: self.barter,
            ActionChoice.Buy: self.buy,
        }

    @property
    def money(self) -> int:
        return self._money

    @money.setter
    def money(self, value: int) -> None:
        self._money = value

    @property
    def target(self) -> Optional[Pirate | Shop]:
        return super().target

    @target.setter
    def target(self, target: Optional[Pirate | Shop]) -> None:
        from .merchant import Shop
        from .pirate import Pirate

        # No target for Work and Barter
        if self.action_choice is ActionChoice.Work and target is not None:
            raise WrongTargetError(self.action_choice)

        # Target must be a Pirate for Barter
        if self.action_choice is ActionChoice.Barter and not isinstance(target, Pirate):
            raise WrongTargetError(ActionChoice.Barter, Pirate)

        # Target must be an Item for Buy
        if self.action_choice is ActionChoice.Buy and not isinstance(target, Shop):
            raise WrongTargetError(ActionChoice.Buy, Shop)

        if Player.target.fset is not None:
            Player.target.fset(self, target)

    def choose_target(self) -> None:
        match self.action_choice:
            case ActionChoice.Buy:
                items = self.simulation.shops
                if items:
                    self.target = random.choice(items)
            case ActionChoice.Barter:
                if self.simulation.alive_pirates:
                    self.target = random.choice(self.simulation.alive_pirates)
            case _:
                self.target = None

    def work(self) -> None:
        """
        Increase the villager's money and happiness by WORK_MONEY and WORK_HAPPINESS respectively.
        """
        self.money += WORK_MONEY
        self.happiness += WORK_HAPPINESS

    def barter(self) -> None:
        """
        Perform a barter with the target pirate, exchanging money and happiness.
        """
        from .pirate import Pirate

        if not isinstance(self.target, Pirate):
            raise WrongTargetError(ActionChoice.Barter, Pirate)

        price = round(self.minimum_price() / BARTER_FACTOR)
        happiness_gain = BARTER_FACTOR * self.maximum_happiness()

        if self.money > price:
            raise ImpossibleActionError(self, f"Not enough money: {self.money}.")

        self.happiness += happiness_gain
        self.money -= price
        self.target.money += price

        self.interact_with(self.target)

    def buy(self) -> None:
        """
        Perform a buy action with the target shop, exchanging money and happiness.
        """
        from .merchant import Shop

        if not isinstance(self.target, Shop):
            raise WrongTargetError(ActionChoice.Buy, Shop)

        price = self.target.price
        happiness_gain = self.happiness_gain(price)

        if self.money > price:
            raise ImpossibleActionError(
                self, f"Not enough money: ({self.money}/{price})."
            )

        self.happiness += happiness_gain
        self.money -= price
        self.target.owner.money += price

        self.interact_with(self.target.owner)

    def happiness_gain(self, price: int) -> int:
        """
        Return the happiness gain for a given price.
        """
        return round(HAPPINESS_GAIN_FACTOR * price)

    def minimum_price(self) -> int:
        """
        Return the minimum price of all the shops.
        """
        return min(shop.price for shop in self.simulation.shops)

    def maximum_happiness(self) -> int:
        """
        Return the maximum happiness of all the players.
        """
        return max(self.happiness_gain(shop.price) for shop in self.simulation.shops)

    @property
    def log(self) -> str:
        return super().log + f"{self.happiness}"

    def house(self, *args, **kwargs) -> House:
        return VillagerHouse(
            self,
            height=5,
            depth=5,
            width=4,
            *args,
            **kwargs,
        )
