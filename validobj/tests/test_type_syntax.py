import pytest

from validobj import parse_input

type Int = int

type FreeVar[T] = list[T]


def test_type_syntax():
    assert parse_input(10, Int) == 10
    # The type var resolves to Any, so we can't do anything else here.
    assert parse_input([1, 2, "3"], FreeVar) == [1, 2, "3"]
