from dataclasses import dataclass
from typing import Optional

from player import Player

from simulation.enums import ActionChoice, PirateActionChoice
from utils import do_with_probability


@dataclass
class PirateCrew:
    money: int = 0
    pirates_at_sea: int = 0


@dataclass(kw_only=True)
class Pirate(Player[PirateActionChoice]):
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
        if (
            self.action_choice is ActionChoice.Expedition
            and choice is not ActionChoice.Expedition
        ):  # Reset expedition state
            self.days_at_sea = 0
            self.crew.pirates_at_sea -= 1

    @property
    def expedition_money_variation(self) -> int:
        return 50 * self.crew.pirates_at_sea * self.days_at_sea

    def explore(self) -> None:
        """
        Perform an expedition to gain money and bounty, and potentially infect the crew.
        """
        # Money gain
        self.crew.money += self.expedition_money_variation

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
            Pirate.EXPEDITION_MORTALITY_RATE(self.food, self.crew.money),
            self.die,
        )

    def thief(self) -> None:
        """
        Attempt to steal money from a villager or merchant.
        """
        ...

    def rest(self) -> None:
        """
        Rest in the village and buy food in exchange of money.
        """
        ...


if __name__ == "__main__":
    crew = PirateCrew()
    pirate = Pirate(crew=crew)
    print(pirate.infection_status)
