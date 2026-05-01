from dataclasses import dataclass

from simulation.enums import ActionChoice, VillagerActionChoice
from simulation.player import Player

WORK_MONEY = 100
WORK_HAPPINESS = 10


@dataclass
class Villager(Player[VillagerActionChoice]):
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

    def work(self) -> None:
        self.money += WORK_MONEY
        self.happiness += WORK_HAPPINESS

    def barter(self) -> None: ...

    def buy(self) -> None: ...


if __name__ == "__main__":
    v = Villager()
