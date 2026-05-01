from dataclasses import dataclass, field

from simulation.enums import ActionChoice, MerchantActionChoice
from simulation.player import Player

BASE_PRICE = 1000  # money
MAX_QUANTITY = 100  # units
MAX_ITEMS = 5  # units
RESTOCK_PERCENTAGE = 10  # %
STORE_CLOSURE = 3  # days


@dataclass
class Item:
    price: int = BASE_PRICE
    max_quantity: int = MAX_QUANTITY
    owned_quantity: int = 0


@dataclass
class Merchant(Player[MerchantActionChoice]):
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

    def restock(self) -> None: ...

    def increase_price(self) -> None: ...

    def decrease_price(self) -> None: ...

    def sell_new_item(self) -> None: ...


if __name__ == "__main__":
    v = Merchant()
