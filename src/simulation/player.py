import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, Optional

from log.config import get_sim_logger

from ..utils import do_with_probability
from .enums import ActionChoice, InfectionStatus
from .exceptions import ImpossibleActionError, WrongTargetError

if TYPE_CHECKING:
    from .simulation import Simulation

TRANSMISSION_RATE = 0.15
INCUBATION_RATE = 0.5
RECOVERY_RATE = 0.10
MORTALITY_RATE = 0.01
IMMUNITY_LOSS_RATE = 0.033

DEFAULT_INFECTION_STATUS = InfectionStatus.Susceptible
DEFAULT_IDLE_PERIOD = 0
DEFAULT_ACTION_CHOICE = None
DEFAULT_TARGET = None

HEAL_COST_FACTOR = 50
HEAL_IDLE_PERIOD = 7

logger = get_sim_logger()


@dataclass
class Player[T](ABC):
    """
    Class representing a player in the simulation.
    """

    simulation: Simulation = field(init=False, repr=False)
    infection_status: InfectionStatus = field(
        init=False, default=DEFAULT_INFECTION_STATUS
    )
    idle_period: int = field(init=False, default=DEFAULT_IDLE_PERIOD)

    _action_choice: Optional[ActionChoice] = field(
        init=False, default=DEFAULT_ACTION_CHOICE
    )
    _target: Optional[T] = field(init=False, default=DEFAULT_TARGET)

    def __str__(self) -> str:
        return f"{self.__class__.__name__} {id(self)}"

    def die(self) -> None:
        """
        Makes the player die
        :return: None
        """
        self.infection_status = InfectionStatus.Dead
        logger.infection(self)

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
        logger.infection(self)

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
        logger.infection(self)

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
        logger.infection(self)

    @property
    def recovered(self) -> bool:
        """
        Whether the player is recovered
        :return: A boolean
        """
        return self.infection_status == InfectionStatus.Recovered

    def lose_immunity(self) -> None:
        self.infection_status = InfectionStatus.Susceptible
        logger.infection(self)

    @property
    def susceptible(self) -> bool:
        """
        Whether the player is susceptible/has lost immunity
        :return: A boolean
        """
        return self.infection_status == InfectionStatus.Susceptible

    def interact_with(self, other: "Player") -> None:
        """
        Makes the player interact with another
        :param other: The other player with whom to interact
        :return: None
        """
        logger.info(f"{self} has interacted with {other}.", theme="INFECTION")
        if self.susceptible:
            if not other.infected:
                return
            do_with_probability(TRANSMISSION_RATE, self.expose)
        elif self.infected:
            if not other.susceptible:
                return
            do_with_probability(TRANSMISSION_RATE, other.expose)

    @property
    def can_play(self) -> bool:
        """
        Whether the player can play this round
        :return: A boolean
        """
        return not self.dead and self.idle_period == 0

    @property
    def action_map(self) -> dict[ActionChoice, Callable[[], None]]:
        """
        The action map for the player
        :return: A dictionary mapping action choices to callables
        """
        return {ActionChoice.Heal: self.heal}

    def step(self) -> None:
        """
        Advance one step in the simulation for the player
        :return: None
        """
        # Decrease idle period by 1, but not below 0
        self.idle_period = max(0, self.idle_period - 1)

        # Infection model specifics
        if self.exposed:
            do_with_probability(INCUBATION_RATE, self.infect)
        elif self.infected:
            _, done = do_with_probability(RECOVERY_RATE, self.recover)
            if not done:  # If not recovered, then perhaps die
                do_with_probability(MORTALITY_RATE, self.die)
        elif self.recovered:
            do_with_probability(IMMUNITY_LOSS_RATE, self.lose_immunity)

        # Perform the chosen action
        if self.can_play:
            choice = self.action_choice
            if choice and (act := self.action_map.get(choice)):
                try:
                    act()
                except ImpossibleActionError:
                    pass

    def heal(self) -> None:
        """
        Heal the player
        :return: None
        """
        cost = self.heal_cost

        if self.money < cost:
            raise ImpossibleActionError(self, f"Not enough money ({self.money}/{cost})")

        self.money -= cost
        self.idle_period = HEAL_IDLE_PERIOD

        logger.infection(
            f"HEAL: {self} is healing. Balance: {self.money}. Idle for {HEAL_IDLE_PERIOD} days."
        )

    @property
    def heal_cost(self) -> int:
        """
        :return: The cost of healing
        """
        shops = self.simulation.shops
        if len(shops) != 0:
            return round(HEAL_COST_FACTOR * (sum(s.price for s in shops) / len(shops)))
        return HEAL_COST_FACTOR * (sum(s.price for s in shops))

    @property
    @abstractmethod
    def money(self) -> int: ...

    @money.setter
    @abstractmethod
    def money(self, value: int) -> None: ...

    @property
    def action_choice(self) -> Optional[ActionChoice]:
        """
        :return: The chosen action for this player
        """
        return self._action_choice

    @action_choice.setter
    def action_choice(self, choice: Optional[ActionChoice]) -> None:
        """
        Set the action choice for this player
        :param choice: The action choice to set
        :return: None
        """
        self._action_choice = choice

    @property
    def target(self) -> Optional[T]:
        """
        :return: The target for the upcoming action
        """
        return self._target

    @target.setter
    def target(self, target: Optional[T]) -> None:
        """
        Set the target for the upcoming action
        :param target: The target to set
        :return: None
        """
        # No target for None action
        if self.action_choice is None and target is not None:
            raise WrongTargetError()

        # No target for Heal action
        if self.action_choice is ActionChoice.Heal and target is not None:
            raise WrongTargetError(ActionChoice.Heal)

        # Cannot target a dead player
        if isinstance(target, Player) and target.dead:
            raise WrongTargetError(message="Cannot target a dead player.")

        self._target = target

    def choose_action(self) -> None:
        """
        Choose an action for this player
        :return: None
        """
        if self.can_play:
            self.action_choice = random.choice(list(self.action_map.keys()) + [None])
        else:
            self.action_choice = None

    @abstractmethod
    def choose_target(self) -> None:
        """
        Choose a target for the upcoming action
        :return: None
        """
