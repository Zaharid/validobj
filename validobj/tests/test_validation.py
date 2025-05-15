import dataclasses
import enum
from collections import namedtuple
from typing import (
    Tuple,
    Set,
    List,
    Mapping,
    Any,
    Union,
    Callable,
    NewType,
    Literal,
    NamedTuple,
)
import sys

try:
    from types import UnionType
except ImportError:  # pragma: nocover
    HAVE_UNION_TYPE = False
else:
    HAVE_UNION_TYPE = True

try:
    from typing import TypedDict
except ImportError:  # pragma: nocover
    HAVE_TYPED_DICT = False
else:
    HAVE_TYPED_DICT = sys.version_info >= (3, 9)

try:
    from typing import Annotated
except ImportError:  # pragma: nocover
    HAVE_ANNOTATED = False
else:
    HAVE_ANNOTATED = True

import pytest
from hypothesis import given
from hypothesis.strategies import (
    builds,
    booleans,
    dictionaries,
    text,
)

from validobj.validation import parse_input, ValidationError, UnionValidationError

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
    connection: dataclasses.InitVar[str] = "localhost"


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
    db["connection"] = "connection"
    return db


metadata_strat = dictionaries(text(), booleans())
dbstrat = builds(Db, metadata=metadata_strat).map(invert_db)


@given(dbstrat)
def test_arbitrary_valid(db):
    parse_input(db, Db)


def test_none():
    assert parse_input(None, None) is None
    with pytest.raises(ValidationError):
        parse_input("Some value", None)


def test_literal():
    assert parse_input(5, Literal[5, Literal[1, 3]]) == 5


def test_newtype():
    Base = Union[str, Literal[5]]
    Derived = NewType("Derived", Base)
    v = 5
    assert parse_input(v, Derived) == 5


@pytest.mark.skipif(not HAVE_UNION_TYPE, reason="Union type not found")
def test_union():
    assert parse_input("READ", Attributes | MemOptions | None) is Attributes.READ
    assert parse_input(None, Attributes | MemOptions | None) is None
    with pytest.raises(UnionValidationError):
        parse_input(1, Attributes | MemOptions)


@pytest.mark.skipif(not HAVE_TYPED_DICT, reason="Typed dict not found")
def test_typed_dict():
    T = TypedDict("T", {"a": Union[str, int], "b": int})
    assert parse_input({"a": 1, "b": 1}, T) == {"a": 1, "b": 1}
    with pytest.raises(ValidationError):
        parse_input({"a": 1}, T)
    with pytest.raises(ValidationError):
        parse_input({"a": "uno", "b": "dos"}, T)
    with pytest.raises(ValidationError):
        parse_input("x", T)
    U = TypedDict("T", {"a": Union[str, int], "b": int}, total=False)
    assert parse_input({"a": 1}, U) == {"a": 1}


def test_namedtuple():
    class X(NamedTuple):
        a: int
        b: str = "hello"
        c: Literal[5, 10] = 10

    Y = namedtuple("Y", ("a", "b", "c"), defaults=(10,))

    assert parse_input([1], X) == (1, "hello", 10)
    assert parse_input([3, "cuatro", 5], X) == (3, "cuatro", 5)
    assert parse_input(["Hello", 1 , {"dos"}], Y) == Y("Hello", 1, {"dos"})

    with pytest.raises(ValidationError):
        parse_input("xx", X)

    with pytest.raises(ValidationError):
        parse_input([], X)

    with pytest.raises(ValidationError):
        parse_input(["xx"], X)

    with pytest.raises(ValidationError):
        parse_input(["xx"]*4, Y)



@pytest.mark.skipif(not HAVE_ANNOTATED, reason="Annotated not found")
def test_annotated():
    T = Annotated[Union[Annotated[int, "bogus"], None], "bogus"]
    assert parse_input(5, T) == 5
    assert parse_input(None, T) is None
    with pytest.raises(ValidationError):
        parse_input("cinco", T)

def test_number_casts():
    float4 = parse_input(4, float)
    assert isinstance(float4, float)
    assert float4 == 4.

    complex4 = parse_input(4, complex)
    assert isinstance(complex4, complex)
    assert complex4 == 4.

    complex45 = parse_input(4.5, complex)
    assert isinstance(complex45, complex)
    assert complex45 == 4.5

    with pytest.raises(ValidationError):
        parse_input(4.5, int)

    with pytest.raises(ValidationError):
        parse_input(4.+0j, int)

    with pytest.raises(ValidationError):
        parse_input(4.+0j, float)
