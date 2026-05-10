import random
from typing import Any, Callable

import pytest

from src.simulation.merchant import MAX_ITEMS, Merchant, Shop
from src.simulation.player import Player
from src.simulation.simulation import Simulation


class ConcretePlayer(Player[Any]):
    def choose_target(self) -> None: ...

    @property
    def money(self) -> int: ...

    @money.setter
    def money(self, value: int) -> None: ...


@pytest.fixture
def player():
    return ConcretePlayer()


@pytest.fixture
def player_with_money(player: ConcretePlayer) -> ConcretePlayer:
    player.money = 100_000
    return player


@pytest.fixture
def merchant_with_shops_factory() -> Callable[[], Merchant]:
    def create_merchant() -> Merchant:
        merchant = Merchant()
        merchant.money = 100_000

        for _ in range(random.randint(1, MAX_ITEMS)):
            merchant.sell_new_item()

        return merchant

    return create_merchant


@pytest.fixture
def simulation_with_shops(
    merchant_with_shops_factory: Callable[[], Merchant],
) -> Simulation:
    m1 = Merchant()
    m2 = Merchant()

    m1.store = [Shop(m1, price=100)]
    m2.store = [Shop(m2, price=200)]

    return Simulation(players=[m1, m2])
