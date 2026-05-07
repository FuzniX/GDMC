import random
from dataclasses import dataclass, field
from typing import Callable, Optional

from .enums import ActionChoice
from .exceptions import ImpossibleActionError, WrongTargetError
from .player import Player

BASE_PRICE = 1000  # money
MAX_QUANTITY = 100  # units
MIN_ITEMS = 1  # units
MAX_ITEMS = 5  # units
RESTOCK_PERCENTAGE = 10  # %
CLOSURE_PERIOD = 3  # days
PRICE_VARIATION = 10  # %
NEW_ITEM_COST = 10000  # money


@dataclass
class Shop:
    owner: "Merchant"
    price: int = BASE_PRICE
    max_quantity: int = MAX_QUANTITY
    owned_quantity: int = 0
    name: str = ""
    is_food: bool = True


@dataclass
class Merchant(Player[int]):
    """
    Class representing a merchant player in the simulation.
    """

    money: int = 0
    store: list[Shop] = field(default_factory=list)
    closure_period: int = field(init=False, default=0)

    @property
    def action_map(self) -> dict[ActionChoice, Callable[[], None]]:
        return super().action_map | {
            ActionChoice.Restock: self.restock,
            ActionChoice.IncreasePrice: self.increase_price,
            ActionChoice.DecreasePrice: self.decrease_price,
            ActionChoice.SellNewItem: self.sell_new_item,
        }

    def step(self) -> None:
        super().step()
        self.closure_period = max(0, self.closure_period - 1)

    @property
    def target(self) -> Optional[int]:
        return super().target

    @target.setter
    def target(self, target: Optional[int]) -> None:
        # No target for Restock and SellNewItem
        if (
            self.action_choice in [ActionChoice.Restock, ActionChoice.SellNewItem]
            and target is not None
        ):
            raise WrongTargetError(self.action_choice)

        # Target must be an integer between MIN_ITEMS and MAX_ITEMS for IncreasePrice and DecreasePrice
        if self.action_choice in [
            ActionChoice.IncreasePrice,
            ActionChoice.DecreasePrice,
        ] and not (isinstance(target, int) and (MIN_ITEMS <= target <= MAX_ITEMS)):
            raise WrongTargetError(
                message=f"Target must be an integer between {MIN_ITEMS} and {MAX_ITEMS} for {self.action_choice.value} action."
            )

        if Player.target.fset is not None:
            Player.target.fset(self, target)

    def choose_target(self) -> None:
        match self.action_choice:
            case ActionChoice.IncreasePrice | ActionChoice.DecreasePrice:
                if self.store:
                    self.target = random.randint(1, len(self.store))
            case _:
                self.target = None

    def restock(self) -> None:
        """
        Restock the merchant's inventory to full capacity and deduct a percentage of the money.
        """
        if self.target is not None:
            raise WrongTargetError(ActionChoice.Restock)

        for item in self.store:
            item.owned_quantity = item.max_quantity

        self.money -= round(self.money * RESTOCK_PERCENTAGE / 100)
        self.closure_period = CLOSURE_PERIOD

    def increase_price(self) -> None:
        """
        Increase the price of the merchant's items by INCREASE_PRICE_PERCENTAGE.
        """
        if not isinstance(self.target, int):
            assert self.action_choice is ActionChoice.IncreasePrice
            raise WrongTargetError(
                message=f"Target must be an integer between {MIN_ITEMS} and {MAX_ITEMS} for {self.action_choice.value} action."
            )

        item = self.store[self.target - 1]
        item.price = round(item.price * (1 + PRICE_VARIATION / 100))

    def decrease_price(self) -> None:
        """
        Decrease the price of the merchant's items by DECREASE_PRICE_PERCENTAGE.
        """
        if not isinstance(self.target, int):
            assert self.action_choice is ActionChoice.DecreasePrice
            raise WrongTargetError(
                message=f"Target must be an integer between {MIN_ITEMS} and {MAX_ITEMS} for {self.action_choice.value} action."
            )

        item = self.store[self.target - 1]
        item.price = round(item.price * (1 - PRICE_VARIATION / 100))

    def sell_new_item(self) -> None:
        """
        Sell a new item to the merchant, deducting money and adding it to the inventory.
        """
        if self.target is not None:
            raise WrongTargetError(ActionChoice.SellNewItem)

        cost = self.new_item_cost

        if len(self.store) == 5:
            raise ImpossibleActionError(
                ActionChoice.SellNewItem,
                message=f"Cannot shop more than {MAX_ITEMS} items.",
            )

        if self.money < cost:
            raise ImpossibleActionError(
                ActionChoice.SellNewItem,
                message=f"Not enough money to sell a new item (cost: {cost}, money: {self.money}).",
            )

        self.money -= cost

        self.store.append(Shop(owner=self))

    @property
    def new_item_cost(self) -> int:
        """
        Return the cost of selling a new item.
        """
        return (len(self.store) + 1) * NEW_ITEM_COST


if __name__ == "__main__":
    m = Merchant()

    m.action_choice = ActionChoice.Restock
    m.target = 4
