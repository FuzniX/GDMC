import pytest

import src.simulation.player as player_module
from src.simulation.enums import InfectionStatus
from src.simulation.player import (
    DEFAULT_ACTION_CHOICE,
    DEFAULT_IDLE_PERIOD,
    DEFAULT_INFECTION_STATUS,
    DEFAULT_TARGET,
)
from tests.simulation.conftest import ConcretePlayer


def status_parametrizer(excluded_status: InfectionStatus) -> list[InfectionStatus]:
    return [s for s in InfectionStatus if s != excluded_status]


def test_instance(player: ConcretePlayer):
    assert isinstance(player, ConcretePlayer)

    # State should be initialized to default values
    assert not hasattr(player, "simulation")
    assert player.infection_status == DEFAULT_INFECTION_STATUS
    assert player.idle_period == DEFAULT_IDLE_PERIOD
    assert player._action_choice == DEFAULT_ACTION_CHOICE
    assert player._target == DEFAULT_TARGET


@pytest.mark.parametrize("reset_status", status_parametrizer(InfectionStatus.Dead))
def test_death(player: ConcretePlayer, reset_status: InfectionStatus):
    assert not player.dead

    # Manual method
    player.infection_status = InfectionStatus.Dead
    assert player.dead

    # Reset state
    player.infection_status = reset_status
    assert not player.dead

    # Intended method
    player.die()
    assert player.dead


@pytest.mark.parametrize("reset_status", status_parametrizer(InfectionStatus.Exposed))
def test_exposure(player: ConcretePlayer, reset_status: InfectionStatus):
    assert not player.exposed

    # Manual method
    player.infection_status = InfectionStatus.Exposed
    assert player.exposed

    # Reset state
    player.infection_status = reset_status
    assert not player.exposed

    # Intended method
    player.expose()
    assert player.exposed


@pytest.mark.parametrize("reset_status", status_parametrizer(InfectionStatus.Infected))
def test_infection(player: ConcretePlayer, reset_status: InfectionStatus):
    assert not player.infected

    # Manual method
    player.infection_status = InfectionStatus.Infected
    assert player.infected

    # Reset state
    player.infection_status = reset_status
    assert not player.infected

    # Intended method
    player.infect()
    assert player.infected


@pytest.mark.parametrize("reset_status", status_parametrizer(InfectionStatus.Recovered))
def test_recovery(player: ConcretePlayer, reset_status: InfectionStatus):
    assert not player.infected

    # Manual method
    player.infection_status = InfectionStatus.Recovered
    assert player.recovered

    # Reset state
    player.infection_status = reset_status
    assert not player.recovered

    # Intended method
    player.recover()
    assert player.recovered


@pytest.mark.parametrize(
    "reset_status", status_parametrizer(InfectionStatus.Susceptible)
)
def test_susceptible(player: ConcretePlayer, reset_status: InfectionStatus):
    assert player.susceptible

    # Any other state
    player.infection_status = reset_status
    assert not player.susceptible

    # Manual method
    player.infection_status = InfectionStatus.Susceptible
    assert player.susceptible

    # Realistic case
    player.recover()

    # Intended method
    player.lose_immunity()
    assert player.susceptible


@pytest.mark.parametrize("status_self", InfectionStatus)
@pytest.mark.parametrize("status_other", InfectionStatus)
def test_interaction(
    monkeypatch: pytest.MonkeyPatch,
    status_self: InfectionStatus,
    status_other: InfectionStatus,
):
    p1 = ConcretePlayer()
    p2 = ConcretePlayer()
    p1.infection_status = status_self
    p2.infection_status = status_other

    # Test with 100% chance of infection
    monkeypatch.setattr(player_module, "TRANSMISSION_RATE", 1.0)
    p1.interact_with(p2)

    if (  # Case where p2 infects p1
        status_self is InfectionStatus.Susceptible
        and status_other is InfectionStatus.Infected
    ):
        assert p1.infection_status is InfectionStatus.Exposed

    elif (  # Case where p1 infects p2
        status_self is InfectionStatus.Infected
        and status_other is InfectionStatus.Susceptible
    ):
        assert p2.infection_status is InfectionStatus.Exposed

    else:  # No infection can occur in any other case
        assert p1.infection_status is status_self
        assert p2.infection_status is status_other

    # Reset state
    p1.infection_status = status_self
    p2.infection_status = status_other

    # Test with 0% chance of infection
    monkeypatch.setattr(player_module, "TRANSMISSION_RATE", 0.0)
    p1.interact_with(p2)

    # No transmission occurs, infection status remains unchanged
    assert p1.infection_status is status_self
    assert p2.infection_status is status_other
