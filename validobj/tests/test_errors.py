import enum
import dataclasses
from typing import List, Mapping, Optional, Literal, NamedTuple

import pytest

from validobj.validation import parse_input
from validobj.errors import (
    UnionValidationError,
    AlternativeDisplay,
    NotAnEnumItemError,
    WrongListItemError,
    WrongFieldError,
    WrongKeysError,
    WrongLiteralError,
)


@dataclasses.dataclass
class Fieldset:
    a: int
    b: int


class E(enum.Enum):
    FIELD1 = 'field1'
    FIELD2 = 'field2'


class X(NamedTuple):
    a: int
    b: str = "hello"
    c: Literal[5, 10] = 10


def test_alternative_display():
    ad = str(
        AlternativeDisplay(
            bad_item='bad',
            alternatives=['could', 'be', 'good'],
            display_all_alternatives=True,
        )
    )
    assert 'could' in ad
    ad = str(AlternativeDisplay(bad_item=['x'], alternatives=[], header='Hello'))
    assert 'Hello' in ad


def test_mismatch_message():
    with pytest.raises(WrongKeysError) as exinfo:
        parse_input({'a': 1, 'x': 2, 'y': 2}, Fieldset)
    assert 'x' in str(exinfo.value)
    with pytest.raises(WrongKeysError) as exinfo:
        parse_input({'a': 1, 'x': 2, 'b': 2}, Fieldset)
    assert 'x' in str(exinfo.value)
    with pytest.raises(WrongKeysError) as exinfo:
        parse_input({'a': 1}, Fieldset)
    assert 'b' in str(exinfo.value)

    e = WrongKeysError(missing={'a'}, unknown={'x'}, valid={'a', 'b'})
    assert 'x' in str(e)


def test_union_error_message():
    with pytest.raises(UnionValidationError) as exinfo:
        parse_input('FIELD3', Optional[E])
    assert 'FIELD1' in str(exinfo.value)
    assert any(isinstance(c, NotAnEnumItemError) for c in exinfo.value.causes)


def test_enum_error():
    e = str(NotAnEnumItemError('FIELD3', E))
    assert 'FIELD1' in e


def test_correct_items():
    with pytest.raises(WrongListItemError) as exinfo:
        parse_input([1, 'x', 2], List[int])
    assert exinfo.value.wrong_index == 1

    with pytest.raises(WrongFieldError) as exinfo:
        parse_input({'a': 1, 'b': 'x'}, Mapping[str, int])
    assert exinfo.value.wrong_field == 'b'

    with pytest.raises(WrongFieldError) as exinfo:
        parse_input({1: 2, 'a': 1}, Mapping[str, int])
    assert exinfo.value.wrong_field == 1

    with pytest.raises(WrongFieldError) as exinfo:
        parse_input({'a': 'uno', 'b': 2}, Fieldset)
    assert exinfo.value.wrong_field == 'a'


def test_literal_error():
    with pytest.raises(WrongLiteralError) as exinfo:
        parse_input(5, Literal[6])
    assert exinfo.value.value == 5
    assert exinfo.value.reference == [6,]
    assert "5" in str(exinfo.value)

    with pytest.raises(WrongLiteralError) as exinfo:
        parse_input(5, Literal[6, Literal[7], 8])
    assert exinfo.value.value == 5
    assert exinfo.value.reference == [6, 7, 8]
    assert "7" in str(exinfo.value)


def test_namedtuple_error():
    with pytest.raises(WrongListItemError) as exinfo:
        parse_input([1, 1], X)
    assert exinfo.value.wrong_index == 1
