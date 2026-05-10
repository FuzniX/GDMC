import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, Optional
import logging

from ..utils import do_with_probability, probability
from .enums import ActionChoice
from .exceptions import ImpossibleActionError, WrongTargetError
from .player import Player

if TYPE_CHECKING:
    from .merchant import Merchant, Shop
    from .villager import Villager


logger = logging.getLogger(__name__)

FOOD_REQUIRED_FOR_EXPEDITION = 1
FOOD_PURCHASE_QUANTITY = 10  # units
STOLEN_MONEY_RATE = 0.20  # %


@dataclass
class PirateCrew:
    money: int = 0
    pirates_at_sea: int = 0


@dataclass
class Pirate(Player["Villager | Merchant | Shop"]):
    """
    Class representing a pirate player in the simulation.
    """

    crew: PirateCrew

    bounty: float = 0
    food: int = 0

    days_at_sea: int = field(init=False, default=0)

    @property
    def expedition_infection_rate(self) -> float:
        return 0.01 * (self.crew.pirates_at_sea + self.days_at_sea)

    @property
    def expedition_mortality_rate(self) -> float:
        return (0.01 * self.days_at_sea) / self.crew.pirates_at_sea

    @property
    def bounty_increase_rate(self) -> float:
        return 1.05**self.days_at_sea

    @property
    def expedition_money_variation(self) -> int:
        return 50 * self.crew.pirates_at_sea * self.days_at_sea

    def at_sea(self) -> bool:
        """
        Returns whether the pirate is at sea or not.
        """
        return self.action_choice == ActionChoice.Expedition

    @property
    def money(self) -> int:
        return self.crew.money

    @money.setter
    def money(self, value: int) -> None:
        self.crew.money = value

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
            self.crew.pirates_at_sea -= 1

        # Add 1 to the pirate count
        elif (
            self.action_choice is not ActionChoice.Expedition
            and choice is ActionChoice.Expedition
        ):
            self.crew.pirates_at_sea += 1

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
            logger.warning(f"explore FAILURE: Pirate {id(self)} doesn't have enough food.")
            raise ImpossibleActionError(
                ActionChoice.Expedition, "Not enough food to explore."
            )

        self.food -= FOOD_REQUIRED_FOR_EXPEDITION

        self.days_at_sea += 1

        # Money gain
        self.money += self.expedition_money_variation

        # Bounty gain
        self.bounty *= self.bounty_increase_rate

        # Infection pirate-specific events
        do_with_probability(self.expedition_infection_rate, self.expose)
        do_with_probability(self.expedition_infection_rate, self.die)

        pirates_at_sea = self.simulation.pirates_in_expedition

        if pirates_at_sea:
            self.interact_with(random.choice(pirates_at_sea))

        logger.info(f"State of the pirate {id(self)} during expedition. Day at the sea : {self.days_at_sea}, Bounty : {self.bounty}, Crew Balance: {self.crew.money}")

    def thief(self) -> None:
        """
        Attempt to steal money from a villager or merchant.
        """

        from .villager import Villager
        from .merchant import Merchant

        if self.target is None or not isinstance(self.target, (Villager, Merchant)):
            raise WrongTargetError(ActionChoice.Theft, (Villager, Merchant))

        if not probability(self.theft_success_rate):
            self.idle_period = self.theft_jail_period
            logger.warning(f"theft FAILURE: Pirate {self} in jail for {self.idle_period} days.")
            return

        stolen_money = round(STOLEN_MONEY_RATE * self.target.money)

        self.money += stolen_money
        self.target.money -= stolen_money

        self.interact_with(self.target)

        logger.info(
            f"theft SUCCESS: Pirate {id(self)} stole {stolen_money}."
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
            raise ImpossibleActionError(
                ActionChoice.Rest, "The target is not a food shop."
            )

        # The crew doesn't have enough money.
        if purchase_price > self.money:
            logger.warning(f"rest FAILURE: not enough money. Pirate {id(self)} Balance: {self.money} ")
            raise ImpossibleActionError(
                ActionChoice.Rest, "Not enough money to buy food at the merchant."
            )

        # Not enough food to buy at the merchant.
        if FOOD_PURCHASE_QUANTITY > self.target.owned_quantity:
            logger.warning(f"rest FAILURE: not enough food to buy at the merchant. Merchant {id(self.target.owner)} Stock: {self.target.owned_quantity} ")
            raise ImpossibleActionError(
                ActionChoice.Rest, "Not enough food to buy at the merchant."
            )

        self.money -= purchase_price
        self.target.owner.money += purchase_price
        self.food += FOOD_PURCHASE_QUANTITY

        # Infection interaction
        self.interact_with(self.target.owner)
        logger.info(f"Pirate {id(self)} bought {self.target}. Balance: {self.money} ")

    @property
    def theft_success_rate(self) -> float:
        """
        The probability of successfully stealing money from a target.
        """
        from .villager import Villager
        from .merchant import Merchant

        assert isinstance(self.target, (Villager, Merchant))

        ratio = self.bounty / self.target.money
        return max(0.1, min(0.9, 0.5 * ratio))

    @property
    def theft_jail_period(self) -> int:
        """
        The amount of days spent in jail after a failed theft attempt.
        """

        from .villager import Villager
        from .merchant import Merchant

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


if __name__ == "__main__":
    crew = PirateCrew(money=1000)
    pirate = Pirate(crew=crew)

    from .merchant import Merchant, Shop
    from .villager import Villager

    pirate.action_choice = ActionChoice.Rest
    merchant = Merchant(money=1000)
    merchant.store = [Shop(merchant, price=10), Shop(merchant, price=20)]
    pirate.target = merchant
    print(pirate.money)
    pirate.step()
    print(pirate.money)
    print(pirate.target.money)
