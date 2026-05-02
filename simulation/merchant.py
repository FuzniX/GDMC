from dataclasses import dataclass, field
from typing import Optional

from simulation.exceptions import WrongTargetError

from .enums import ActionChoice, MerchantActionChoice
from .player import Player

BASE_PRICE = 1000  # money
MAX_QUANTITY = 100  # units
MIN_ITEMS = 1  # units
MAX_ITEMS = 5  # units
RESTOCK_PERCENTAGE = 10  # %
STORE_CLOSURE = 3  # days
PRICE_VARIATION = 10  # %


@dataclass
class Item:
    price: int = BASE_PRICE
    max_quantity: int = MAX_QUANTITY
    owned_quantity: int = 0


@dataclass
class Merchant(Player[MerchantActionChoice, int]):
    money: int = 0
    inventory: list[Item] = field(default_factory=list)

    def step(self) -> None:
        super().step()

        match self._action_choice:
            case ActionChoice.Restock:
                self.restock()
            case ActionChoice.IncreasePrice:
                self.increase_price()
            case ActionChoice.DecreasePrice:
                self.decrease_price()
            case ActionChoice.SellNewItem:
                self.sell_new_item()
            case _:
                pass

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

        Player.target.fset(self, target)

    def restock(self) -> None: ...

    def increase_price(self) -> None: ...

    def decrease_price(self) -> None: ...

    def sell_new_item(self) -> None: ...


if __name__ == "__main__":
    m = Merchant()

    m.action_choice = ActionChoice.Restock
    m.target = 4
