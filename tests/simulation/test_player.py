from typing import Any, Callable, Optional

import pytest

from src.simulation.enums import ActionChoice
from src.simulation.exceptions import WrongTargetError
from src.simulation.player import (
    DEFAULT_ACTION_CHOICE,
    DEFAULT_TARGET,
    HEAL_COST_FACTOR,
    HEAL_IDLE_PERIOD,
    Player,
)
from src.simulation.simulation import Simulation
from tests.simulation.conftest import ConcretePlayer


class TestPlayer:
    @pytest.mark.parametrize("idle_period", [1, 3, 7, 999])
    def test_can_play(self, player: ConcretePlayer, idle_period: int) -> None:
        # Ensure initial environment is clean
        assert not player.dead
        assert player.idle_period == 0
        assert player.can_play

        # Player is idle, cannot play
        player.idle_period = idle_period
        assert not player.can_play

        # Reset state
        player.idle_period = 0

        # Player is dead, cannot play
        player.die()
        assert not player.can_play

    def test_action_map(self, player: ConcretePlayer) -> None:
        action_map = player.action_map

        assert isinstance(action_map, dict)

        for choice, function in action_map.items():
            assert isinstance(choice, ActionChoice)
            assert isinstance(function, Callable)

    @pytest.mark.parametrize("choice", ActionChoice)
    def test_action_choice(self, player: ConcretePlayer, choice: ActionChoice) -> None:
        # Initial state
        assert player.action_choice == DEFAULT_ACTION_CHOICE

        # Set choice
        player.action_choice = choice
        assert player.action_choice == choice

    @pytest.mark.parametrize("target", [None, 42, ConcretePlayer()])
    def test_target(self, player: ConcretePlayer, target: Optional[Any]) -> None:
        # Initial state
        assert player.target == DEFAULT_TARGET

        # No action is provided, cannot have a target.
        if target is None:  # Exception case where we explicitly set no target
            player.target = target
            assert player.target is None
        else:
            with pytest.raises(WrongTargetError):
                player.target = target

        # Reset state
        player.target = DEFAULT_TARGET

        player.action_choice = ActionChoice.Heal

        # Heal Action is set, target should be None
        if target is None:  # Exception case where we explicitly set no target
            player.target = target
            assert player.target is None
        else:
            with pytest.raises(WrongTargetError):
                player.target = target

        # Reset state
        player.target = DEFAULT_TARGET

        player.action_choice = ActionChoice.Theft  # Any ActionChoice

        if isinstance(target, Player):
            target.die()

            # Cannot set target to a dead player
            with pytest.raises(WrongTargetError):
                player.target = target
        else:
            player.target = target
            assert player.target == target

    @pytest.mark.repeat(10)
    def test_choose_action(self, player: ConcretePlayer) -> None:
        player.choose_action()

        if player.can_play:
            assert (
                player.action_choice in player.action_map
                or player.action_choice is None
            )
        else:
            assert player.action_choice is None

    def test_heal(
        self,
        player: ConcretePlayer,
        player_with_money: ConcretePlayer,
        simulation_with_shops: Simulation,
    ) -> None:
        player_with_money.simulation = simulation_with_shops

        initial_money = player_with_money.money
        cost = HEAL_COST_FACTOR * 150

        # Can heal
        player_with_money.heal()

        assert player_with_money.money == initial_money - cost
        assert player_with_money.idle_period == HEAL_IDLE_PERIOD

    def test_step(self, player: ConcretePlayer) -> None: ...
