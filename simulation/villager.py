from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from .enums import ActionChoice, VillagerActionChoice
from .exceptions import WrongTargetError
from .player import Player

if TYPE_CHECKING:
    from .merchant import Merchant
    from .pirate import Pirate

WORK_MONEY = 100
WORK_HAPPINESS = 10


@dataclass
class Villager(Player[VillagerActionChoice, "Pirate | Merchant"]):
    happiness: int = 0
    money: int = 0

    def step(self) -> None:
        super().step()

        match self.action_choice:
            case ActionChoice.Work:
                self.work()
            case ActionChoice.Barter:
                self.barter()
            case ActionChoice.Buy:
                self.buy()
            case ActionChoice.Heal:
                self.heal()
            case _:
                pass

    @property
    def target(self) -> Optional["Pirate | Merchant"]:
        return super().target

    @target.setter
    def target(self, target: Optional["Pirate | Merchant"]) -> None:
        from .merchant import Merchant

        # No target for Work and Barter
        if (
            self.action_choice in [ActionChoice.Work, ActionChoice.Barter]
            and target is not None
        ):
            raise WrongTargetError(self.action_choice)

        # Target must be a Merchant for Buy
        if self.action_choice is ActionChoice.Buy and not isinstance(target, Merchant):
            raise WrongTargetError(ActionChoice.Buy, Merchant)

        Player.target.fset(self, target)

    def work(self) -> None:
        self.money += WORK_MONEY
        self.happiness += WORK_HAPPINESS

    def barter(self) -> None: ...

    def buy(self) -> None: ...


if __name__ == "__main__":
    v = Villager()
