import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, Optional

from log.config import get_sim_logger

from ..utils import do_with_probability, probability
from .enums import ActionChoice
from .exceptions import ImpossibleActionError, WrongTargetError
from .player import Player

if TYPE_CHECKING:
    from .merchant import Merchant, Shop
    from .villager import Villager

FOOD_REQUIRED_FOR_EXPEDITION = 1
FOOD_PURCHASE_QUANTITY = 10  # units
STOLEN_MONEY_RATE = 0.20  # %

DEFAULT_BOUNTY = 0
DEFAULT_FOOD = 0
DEFAULT_DAYS_AT_SEA = 0

logger = get_sim_logger()


@dataclass
class Pirate(Player["Villager | Merchant | Shop"]):
    """
    Class representing a pirate player in the simulation.
    """

    bounty: float = DEFAULT_BOUNTY
    food: int = DEFAULT_FOOD

    days_at_sea: int = field(init=False, default=DEFAULT_DAYS_AT_SEA)

    @property
    def expedition_infection_rate(self) -> float:
        return 0.01 * (len(self.simulation.pirates_in_expedition) + self.days_at_sea)

    @property
    def expedition_mortality_rate(self) -> float:
        return (0.01 * self.days_at_sea) / len(self.simulation.pirates_in_expedition)

    @property
    def bounty_increase_rate(self) -> float:
        return 1.05**self.days_at_sea

    @property
    def expedition_money_variation(self) -> int:
        return 50 * len(self.simulation.pirates_in_expedition) * self.days_at_sea

    @property
    def at_sea(self) -> bool:
        """
        Returns whether the pirate is at sea or not.
        """
        return self.action_choice == ActionChoice.Expedition

    @property
    def money(self) -> int:
        return self.simulation.pirate_money

    @money.setter
    def money(self, value: int) -> None:
        self.simulation.pirate_money = value

    @property
    def action_map(self) -> dict[ActionChoice, Callable[[], None]]:
        return super().action_map | {
            ActionChoice.Expedition: self.explore,
            ActionChoice.Theft: self.thief,
            ActionChoice.Rest: self.rest,
        }

    @property
    def action_choice(self) -> Optional[ActionChoice]:
        return super().action_choice

    @action_choice.setter
    def action_choice(self, choice: Optional[ActionChoice]) -> None:
        # Reset expedition state
        if (
            self.action_choice is ActionChoice.Expedition
            and choice is not ActionChoice.Expedition
        ):
            self.days_at_sea = 0

        if Player.action_choice.fset is not None:
            Player.action_choice.fset(self, choice)

    @property
    def target(self) -> Optional[Villager | Merchant | Shop]:
        return super().target

    @target.setter
    def target(self, target: Optional[Villager | Merchant | Shop]) -> None:
        from .merchant import Merchant, Shop
        from .villager import Villager

        # No target for expedition
        if self.action_choice is ActionChoice.Expedition and target is not None:
            raise WrongTargetError(ActionChoice.Expedition)

        # Villager or Merchant target required for theft
        if self.action_choice is ActionChoice.Theft and not isinstance(
            target, (Villager, Merchant)
        ):
            raise WrongTargetError(ActionChoice.Theft, (Villager, Merchant))

        # Shop target required for rest
        if self.action_choice is ActionChoice.Rest and not (
            isinstance(target, Shop) and target.is_food
        ):
            raise WrongTargetError(
                ActionChoice.Rest, Shop, message="The target must be a food shop."
            )

        if Player.target.fset is not None:
            Player.target.fset(self, target)

    def choose_target(self) -> None:
        match self.action_choice:
            case ActionChoice.Theft:
                people = self.simulation.villagers + self.simulation.merchants
                if people:
                    self.target = random.choice(people)
            case ActionChoice.Rest:
                food_shops = [s for s in self.simulation.shops if s.is_food]
                if food_shops:
                    self.target = random.choice(food_shops)
            case _:
                self.target = None

    def explore(self) -> None:
        """
        Perform an expedition to gain money and bounty, and potentially infect the crew.
        """
        if not self.has_enough_food:
            raise ImpossibleActionError(self, "Not enough food.")

        self.food -= FOOD_REQUIRED_FOR_EXPEDITION

        self.days_at_sea += 1

        # Money gain
        self.money += self.expedition_money_variation

        # Bounty gain
        self.bounty *= self.bounty_increase_rate

        # Infection pirate-specific events
        do_with_probability(self.expedition_infection_rate, self.expose)
        do_with_probability(self.expedition_infection_rate, self.die)

        pirates_at_sea = [p for p in self.simulation.pirates_in_expedition if p != self]

        if pirates_at_sea:
            self.interact_with(random.choice(pirates_at_sea))

        logger.action(
            f"State of the pirate {self} during expedition. Day at the sea : {self.days_at_sea}, Bounty : {self.bounty}, Crew Balance: {self.crew.money}"
        )

    def thief(self) -> None:
        """
        Attempt to steal money from a villager or merchant.
        """

        from .merchant import Merchant
        from .villager import Villager

        if self.target is None or not isinstance(self.target, (Villager, Merchant)):
            raise WrongTargetError(ActionChoice.Theft, (Villager, Merchant))

        if not probability(self.theft_success_rate):
            self.idle_period = self.theft_jail_period
            logger.action(f"theft FAILURE: {self} in jail for {self.idle_period} days.")
            return

        stolen_money = round(STOLEN_MONEY_RATE * self.target.money)

        self.money += stolen_money
        self.target.money -= stolen_money

        self.interact_with(self.target)

        logger.action(
            f"theft SUCCESS: {self} stole {stolen_money}."
            f"Pirate Balance: {self.money}, Victim Balance: {self.target.money}"
        )

    def rest(self) -> None:
        """
        Rest in the village and buy food in exchange of money.
        """
        from .merchant import Shop

        if self.target is None or not isinstance(
            self.target, Shop
        ):  # Should never be the case, but security check
            raise WrongTargetError(ActionChoice.Rest, Shop)

        purchase_price = FOOD_PURCHASE_QUANTITY * self.target.price

        if not self.target.is_food:
            raise ImpossibleActionError(self, "The target is not a food shop.")

        # The crew doesn't have enough money.
        if purchase_price > self.money:
            raise ImpossibleActionError(
                self,
                f"Not enough money to buy food at the merchant ({self.money}/{purchase_price}).",
            )

        # Not enough food to buy at the merchant.
        if FOOD_PURCHASE_QUANTITY > self.target.owned_quantity:
            raise ImpossibleActionError(
                self,
                f"Not enough food to buy at the merchant ({self.target.owned_quantity}/{FOOD_PURCHASE_QUANTITY}).",
            )

        self.money -= purchase_price
        self.target.owner.money += purchase_price
        self.food += FOOD_PURCHASE_QUANTITY

        # Infection interaction
        self.interact_with(self.target.owner)
        logger.action(f"{self} bought {self.target}. Balance: {self.money} ")

    @property
    def theft_success_rate(self) -> float:
        """
        The probability of successfully stealing money from a target.
        """
        from .merchant import Merchant
        from .villager import Villager

        assert isinstance(self.target, (Villager, Merchant))

        ratio = self.bounty / self.target.money
        return max(0.1, min(0.9, 0.5 * ratio))

    @property
    def theft_jail_period(self) -> int:
        """
        The amount of days spent in jail after a failed theft attempt.
        """

        from .merchant import Merchant
        from .villager import Villager

        assert isinstance(self.target, (Villager, Merchant))

        target_severity = self.target.money // 5000
        bounty_multiplier = 1 + (self.bounty / 10000)

        total_days = (3 + target_severity) * bounty_multiplier

        # Between 2 and 20 days
        return max(2, min(20, round(total_days)))

    @property
    def has_enough_food(self) -> int:
        """
        Whether the pirate has enough food to be at sea.
        """
        return self.food >= FOOD_REQUIRED_FOR_EXPEDITION
