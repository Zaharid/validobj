import pytest
import dataclasses
from typing import Any

try:
    from validobj.custom import Parser, Validator, InputType
except ImportError:  # pragma: nocover
    HAVE_CUSTOM = False
else:
    HAVE_CUSTOM = True

from validobj import parse_input, ValidationError


@pytest.mark.skipif(not HAVE_CUSTOM, reason="Custom type not found")
def test_custom():
    def my_float(inp: str) -> float:
        return float(inp) + 1

    MyFloat = Parser(my_float)
    assert MyFloat.__origin__ is float
    assert isinstance(MyFloat.__metadata__[0], InputType)
    assert isinstance(MyFloat.__metadata__[1], Validator)

    @dataclasses.dataclass
    class Container:
        value: MyFloat

    assert parse_input({"value": "5"}, Container) == Container(value=6)
    with pytest.raises(ValidationError):
        parse_input({"value": 5}, Container)


@pytest.mark.skipif(not HAVE_CUSTOM, reason="Custom type not found")
def test_no_annotations():
    def my_float(inp):
        return float(inp) + 1

    MyFloat = Parser(my_float)
    assert MyFloat.__origin__ is Any
    assert parse_input(5, MyFloat) == 6.0

@pytest.mark.skipif(not HAVE_CUSTOM, reason="Custom type not found")
def test_bad_func():
    def noparams() -> str:
        return "wrong" # pragma: nocover
    with pytest.raises(ValueError):
        Parser(noparams)
