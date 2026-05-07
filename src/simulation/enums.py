from enum import Enum, auto
from typing import Literal


class InfectionStatus(Enum):
    Susceptible = auto()
    Exposed = auto()
    Infected = auto()
    Recovered = auto()
    Dead = auto()


class ActionChoice(Enum):
    # Common
    Heal = "heal"

    # Pirate
    Expedition = "expedition"
    Theft = "theft"
    Rest = "rest"

    # Villager
    Work = "work"
    Barter = "barter"
    Buy = "buy"

    # Merchant
    Restock = "restock"
    IncreasePrice = "increase_price"
    DecreasePrice = "decrease_price"
    SellNewItem = "sell_new_item"


PirateActionChoice = Literal[
    ActionChoice.Heal,
    ActionChoice.Expedition,
    ActionChoice.Theft,
    ActionChoice.Rest,
]

VillagerActionChoice = Literal[
    ActionChoice.Heal,
    ActionChoice.Work,
    ActionChoice.Barter,
    ActionChoice.Buy,
]

MerchantActionChoice = Literal[
    ActionChoice.Heal,
    ActionChoice.Restock,
    ActionChoice.IncreasePrice,
    ActionChoice.DecreasePrice,
    ActionChoice.SellNewItem,
]
