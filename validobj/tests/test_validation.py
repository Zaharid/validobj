import dataclasses
import enum
from typing import Tuple, Set, List, Mapping, Any, Union, Callable, NewType

import pytest
from hypothesis import given
from hypothesis.strategies import builds, register_type_strategy, booleans

from validobj.validation import parse_input, ValidationError

stralias = NewType('stralias', str)


class Attributes(enum.Flag):
    READ = enum.auto()
    WRITE = enum.auto()
    EXECUTE = enum.auto()


class MemOptions(enum.Enum):
    SMALL = 'small'
    MEDIUM = 'medium'
    BIG = 'big'


@dataclasses.dataclass(frozen=True)
class Flag:
    name: stralias


@dataclasses.dataclass
class Row:
    key: str
    values: Tuple[int, int, int]


@dataclasses.dataclass
class Db:
    metadata: Mapping[str, Any]
    flags: Set[Flag]
    rows: List[Row]
    size: MemOptions = MemOptions.SMALL
    attributes: Attributes = Attributes.READ | Attributes.WRITE


good_inp = {
    'flags': [{'name': 'f1'}, {'name': 'f2'}],
    'metadata': {'author': 'Zahari'},
    'rows': [
        {'key': 'Hello', 'values': [1, 2, 3]},
        {'key': 'World', 'values': [4, 5, 6]},
    ],
    'size': 'MEDIUM',
    'attributes': ['READ', 'WRITE', 'EXECUTE'],
}

bad_inp = [
    ('xx', int),
    ('xx', (int, List)),
    ([1, 'xx', 2], Union[int, List[int]]),
    ([1, 'x', 2], Tuple[int, ...]),
    ('xx', Tuple[str]),
    (['xx', 'yy'], Tuple[str]),
    (['xx', 5], Tuple[str, str]),
    (5, Row),
    ({'key': 'OK', 'unknown': 'Bad'}, Row),
    ({'key': 'OK', 'values': [1, 2, 3], 'unknown': 'Bad'}, Row),
    ({'key': 'OK', 'values': [1, "2", 3]}, Row),
    (5, Mapping[str, str]),
    ({'x': 5}, Mapping[str, str]),
    ({5: 'x'}, Mapping[str, str]),
    ({'key': 'OK'}, Row),
    (5, MemOptions),
    ('MEDIUMBIG', MemOptions),
    (['RED', 'YELLOW'], Attributes),
]


def test_good_inp():
    expected_res = Db(
        metadata=good_inp['metadata'],
        flags={Flag('f1'), Flag('f2')},
        rows=[Row('Hello', (1, 2, 3)), Row('World', (4, 5, 6))],
        size=MemOptions.MEDIUM,
        attributes=Attributes.READ | Attributes.WRITE | Attributes.EXECUTE,
    )
    assert parse_input(good_inp, Db) == expected_res


def test_bad_inp():
    for k in bad_inp:
        with pytest.raises(ValidationError):
            parse_input(*k)


def test_not_supported():
    with pytest.raises(NotImplementedError):
        parse_input(5, Callable[[int], set])


def test_collections():
    assert parse_input([1, 2, 3], frozenset) == frozenset((1, 2, 3))
    with pytest.raises(ValidationError):
        parse_input([{1}, 2, 3], frozenset)
    with pytest.raises(ValidationError):
        parse_input("X", frozenset)


register_type_strategy(Any, booleans())


def invert_db(db):
    db = dataclasses.asdict(db)
    db['flags'] = list(map(dataclasses.asdict, db['flags']))

    def invert_row(row):
        # row = dataclasses.asdict(row)
        row['values'] = list(row['values'])
        return row

    db['rows'] = list(map(invert_row, db['rows']))
    db['metadata'] = dict(db['metadata'])
    db['size'] = db['size'].name
    db['attributes'] = list(
        m
        for m in Attributes.__members__
        if Attributes.__members__[m] in db['attributes']
    )
    return db


dbstrat = builds(Db).map(invert_db)


@given(dbstrat)
def test_arbitrary_valid(db):
    parse_input(db, Db)

def test_none():
    assert parse_input(None, None) is None
    with pytest.raises(ValidationError):
        parse_input("Some value", None)
