from typing import Any
import dataclasses

import pytest

from validobj import parse_input, ValidationError

@dataclasses.dataclass
class Linked:
    value: Any
    parents: Linked | list[Linked] | None = None

@dataclasses.dataclass
class Grandparent:
    grandpa_field: int = 3

@dataclasses.dataclass
class Parent(Grandparent):
    parent_field: int = 1
    override_field: str = 'parent'

@dataclasses.dataclass
class Child(Parent):
    child_field: int = 2
    override_field: int = 3


def test_delayed_annotations():
    inp = {'value': 1, 'parents': {'value': 2, 'parents': [{'value': 3}, {'value': 4, 'parents': {'value': 5}}]}}
    assert parse_input(inp, Linked).parents.value == 2

def test_derived_dataclasses():
    inp = {'child_field': 3, 'parent_field': 4, 'override_field': 5, 'grandpa_field': 10}
    res = parse_input(inp, Child)
    assert res.child_field == 3
    assert res.parent_field == 4
    assert res.override_field == 5
    assert res.grandpa_field == 10

    with pytest.raises(ValidationError):
        parse_input({'override_field': 'x'}, Child)





