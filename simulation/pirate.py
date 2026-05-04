from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from utils import do_with_probability, probability

from .enums import ActionChoice, PirateActionChoice
from .exceptions import ImpossibleActionError, WrongTargetError
from .player import Player

if TYPE_CHECKING:
    from .merchant import Item, Merchant
    from .villager import Villager

FOOD_PURCHASE_QUANTITY = 10  # units
STOLEN_MONEY_RATE = 0.20  # %


@dataclass
class PirateCrew:
    money: int = 0
    pirates_at_sea: int = 0


@dataclass(kw_only=True)
class Pirate(Player[PirateActionChoice, "Villager | Merchant | Item"]):
    """
    Class representing a pirate player in the simulation.
    """

    crew: PirateCrew

    bounty: int = 0
    food: int = 0

    days_at_sea: int = 0

    @staticmethod
    def EXPEDITION_INFECTION_RATE(days: int, pirates: int) -> float:
        return 0.01 * (pirates + days)

    @staticmethod
    def EXPEDITION_MORTALITY_RATE(days: int, pirates: int) -> float:
        return (0.01 * days) / pirates

    @property
    def money(self) -> int:
        return self.crew.money

    @money.setter
    def money(self, value: int) -> None:
        self.crew.money = value

    def step(self) -> None:
        super().step()

        if self.can_play:
            match self.action_choice:
                case ActionChoice.Expedition:
                    self.explore()
                case ActionChoice.Theft:
                    self.thief()
                case ActionChoice.Rest:
                    self.rest()
                case ActionChoice.Heal:
                    self.heal()
                case _:
                    pass

    @property
    def action_choice(self) -> Optional[PirateActionChoice]:
        return super().action_choice

    @action_choice.setter
    def action_choice(self, choice: Optional[PirateActionChoice]) -> None:
        # Reset expedition state
        if (
            self.action_choice is ActionChoice.Expedition
            and choice is not ActionChoice.Expedition
        ):
            self.days_at_sea = 0
            self.crew.pirates_at_sea -= 1

        elif (
            self.action_choice is not ActionChoice.Expedition
            and choice is ActionChoice.Expedition
        ):
            self.crew.pirates_at_sea += 1

        if Player.action_choice.fset is not None:
            Player.action_choice.fset(self, choice)

    @property
    def target(self) -> Optional["Villager | Merchant | Item"]:
        return super().target

    @target.setter
    def target(self, target: Optional["Villager | Merchant | Item"]) -> None:
        from .merchant import Merchant
        from .villager import Villager

        # No target for expedition
        if self.action_choice is ActionChoice.Expedition and target is not None:
            raise WrongTargetError(ActionChoice.Expedition)

        # Villager or Merchant target required for theft
        if self.action_choice is ActionChoice.Theft and not isinstance(
            target, (Villager, Merchant)
        ):
            raise WrongTargetError(ActionChoice.Theft, (Villager, Merchant))

        # Item target required for rest
        if self.action_choice is ActionChoice.Rest and not isinstance(target, Item):
            raise WrongTargetError(ActionChoice.Rest, Item)

        if Player.target.fset is not None:
            Player.target.fset(self, target)

    @property
    def expedition_money_variation(self) -> int:
        return 50 * self.crew.pirates_at_sea * self.days_at_sea

    def explore(self) -> None:
        """
        Perform an expedition to gain money and bounty, and potentially infect the crew.
        """
        self.days_at_sea += 1

        # Money gain
        self.money += self.expedition_money_variation

        # Bounty gain
        self.bounty *= round(1.05**self.days_at_sea)

        # Infection pirate-specific events
        do_with_probability(
            Pirate.EXPEDITION_INFECTION_RATE(
                self.days_at_sea, self.crew.pirates_at_sea
            ),
            self.expose,
        )
        do_with_probability(
            Pirate.EXPEDITION_MORTALITY_RATE(self.food, self.money),
            self.die,
        )

    def thief(self) -> None:
        """
        Attempt to steal money from a villager or merchant.
        """
        if self.target is None or not isinstance(self.target, (Villager, Merchant)):
            raise WrongTargetError(ActionChoice.Theft, (Villager, Merchant))

        if not probability(self.theft_success_rate):
            self.idle_period = self.theft_jail_period
            return

        stolen_money = round(STOLEN_MONEY_RATE * self.target.money)

        self.money += stolen_money
        self.target.money -= stolen_money

        self.interact_with(self.target)

    def rest(self) -> None:
        """
        Rest in the village and buy food in exchange of money.
        """
        from .merchant import Item

        if self.target is None or not isinstance(
            self.target, Item
        ):  # Should never be the case, but security check
            raise WrongTargetError(ActionChoice.Rest, Item)

        purchase_price = FOOD_PURCHASE_QUANTITY * self.target.price

        # The crew doesn't have enough money.
        if purchase_price > self.money:
            raise ImpossibleActionError(
                ActionChoice.Rest, "Not enough money to buy food at the merchant."
            )

        self.money -= purchase_price
        self.target.owner.money += purchase_price
        self.food += FOOD_PURCHASE_QUANTITY

        # Infection interaction
        self.interact_with(self.target.owner)

    @property
    def theft_success_rate(self) -> float:
        """
        The probability of successfully stealing money from a target.
        """
        ...

    @property
    def theft_jail_period(self) -> int:
        """
        The amount of days spent in jail after a failed theft attempt.
        """
        ...


if __name__ == "__main__":
    crew = PirateCrew(money=1000)
    pirate = Pirate(crew=crew)

    from .merchant import Item, Merchant
    from .villager import Villager

    pirate.action_choice = ActionChoice.Rest
    merchant = Merchant(money=1000)
    merchant.inventory = [Item(merchant, price=10), Item(merchant, price=20)]
    pirate.target = merchant
    print(pirate.money)
    pirate.step()
    print(pirate.money)
    print(pirate.target.money)
