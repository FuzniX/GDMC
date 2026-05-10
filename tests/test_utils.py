from typing import Any, Optional

import pytest

from src.utils import do_with_probability, probability


@pytest.mark.repeat(100)
def test_probability(random_probability: float):
    assert isinstance(probability(random_probability), bool)


@pytest.mark.repeat(100)
@pytest.mark.parametrize("expected_result", [42, "Hello world!", None])
def test_do_with_probability(random_probability: float, expected_result: Optional[Any]):
    result, done = do_with_probability(random_probability, lambda: expected_result)

    assert isinstance(done, bool)
    if done:
        assert result == expected_result
    else:
        assert result is None
