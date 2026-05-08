import random

import pytest


@pytest.fixture
def random_probability() -> float:
    return random.random()
