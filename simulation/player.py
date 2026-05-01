from dataclasses import dataclass
from typing import Optional

from simulation.enums import ActionChoice, InfectionStatus
from utils import do_with_probability

TRANSMISSION_RATE = 0.15
INCUBATION_RATE = 0.5
RECOVERY_RATE = 0.1
MORTALITY_RATE = 0.01
IMMUNITY_LOSS_RATE = 0.033


@dataclass
class Player[T: ActionChoice]:
    """
    Class representing a player in the simulation.
    """

    infection_status: InfectionStatus = InfectionStatus.Susceptible
    _action_choice: Optional[T] = None

    def die(self) -> None:
        """
        Makes the player die
        :return: None
        """
        self.infection_status = InfectionStatus.Dead

    @property
    def dead(self) -> bool:
        """
        Whether the player is dead
        :return: A boolean
        """
        return self.infection_status == InfectionStatus.Dead

    def expose(self) -> None:
        """
        Makes the player exposed
        :return: None
        """
        self.infection_status = InfectionStatus.Exposed

    @property
    def exposed(self) -> bool:
        """
        Whether the player is exposed
        :return: A boolean
        """
        return self.infection_status == InfectionStatus.Exposed

    def infect(self) -> None:
        """
        Makes the player infected
        :return: None
        """
        self.infection_status = InfectionStatus.Infected

    @property
    def infected(self) -> bool:
        """
        Whether the player is infected
        :return: A boolean
        """
        return self.infection_status == InfectionStatus.Infected

    def recover(self) -> None:
        """
        Makes the player recovered
        :return: None
        """
        self.infection_status = InfectionStatus.Recovered

    @property
    def recovered(self) -> bool:
        """
        Whether the player is recovered
        :return: A boolean
        """
        return self.infection_status == InfectionStatus.Recovered

    def lose_immunity(self) -> None:
        self.infection_status = InfectionStatus.Susceptible

    @property
    def susceptible(self) -> bool:
        """
        Whether the player is susceptible/has lost immunity
        :return: A boolean
        """
        return self.infection_status == InfectionStatus.Susceptible

    @property
    def can_play(self) -> bool:
        """
        Whether the player can play this round
        :return: A boolean
        """
        return self.dead

    def interact_with(self, other: "Player") -> None:
        """
        Makes the player interact with another
        :param other: The other player with whom to interact
        :return: None
        """
        if self.susceptible:
            if not other.infected:
                return
            do_with_probability(TRANSMISSION_RATE, self.expose)
        elif self.infected:
            if not other.susceptible:
                return
            do_with_probability(TRANSMISSION_RATE, other.expose)

    def step(self) -> None:
        """
        Advance one step in the simulation for the player
        :return: None
        """
        if self.exposed:
            do_with_probability(INCUBATION_RATE, self.infect)
        elif self.infected:
            _, done = do_with_probability(RECOVERY_RATE, self.recover)
            if not done:
                do_with_probability(MORTALITY_RATE, self.die)
        elif self.recovered:
            do_with_probability(IMMUNITY_LOSS_RATE, self.lose_immunity)

    def heal(self) -> None:
        """
        Heal the player
        :return: None
        """
        ...

    @property
    def action_choice(self) -> Optional[T]:
        """
        :return: The chosen action for this player
        """
        return self._action_choice

    @action_choice.setter
    def action_choice(self, choice: Optional[T]) -> None:
        """
        Set the action choice for this player
        :param choice: The action choice to set
        :return: None
        """
        self._action_choice = choice


if __name__ == "__main__":
    p1 = Player()
    p2 = Player()
    p = lambda: print(p1.infection_status, p2.infection_status)

    p1.expose()

    for _ in range(10):
        p1.step()
        p()
