from typing import NamedTuple, TypedDict, Optional
import dataclasses

import validobj


class C(TypedDict):
    a: 'A'
    b: 'B'
    c: Optional['C'] = None


class B(NamedTuple):
    a0: 'A'
    a1: 'A'


@dataclasses.dataclass
class A:
    children: list['A']


def test_dataclass():
    assert validobj.parse_input({"children": [{"children": []}]}, A)


def test_namedtuple():
    assert validobj.parse_input([{"children": []}, {"children": []}], B)


def test_typeddict():
    assert validobj.parse_input(
        {
            'a': {'children': [{'children': []}]},
            'b': [{"children": []}, {"children": []}],
            'c': None,
        },
        C,
    )
