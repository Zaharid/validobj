from typing import Any
import dataclasses

from validobj import parse_input

@dataclasses.dataclass
class Linked:
    value: Any
    parents: Linked | list[Linked] | None = None


def test_delayed_annotations():
    inp = {'value': 1, 'parents': {'value': 2, 'parents': [{'value': 3}, {'value': 4, 'parents': {'value': 5}}]}}
    assert parse_input(inp, Linked).parents.value == 2


