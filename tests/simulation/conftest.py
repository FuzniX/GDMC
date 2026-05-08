from typing import Any

import pytest

from src.simulation.player import Player


class ConcretePlayer(Player[Any]):
    def choose_target(self) -> None: ...


@pytest.fixture
def player():
    return ConcretePlayer()
