import enum
import dataclasses
from typing import List, Mapping

from validobj.validation import parse_input
from validobj.errors import (
    AlternativeDisplay,
    NotAnEnumItemError,
    WrongListItemError,
    WrongFieldError,
    WrongKeysError
)


@dataclasses.dataclass
class Fieldset:
    a: int
    b: int


class E(enum.Enum):
    FIELD1 = 'field1'
    FIELD2 = 'field2'


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
    try:
        parse_input({'a': 1, 'x':2, 'y':2}, Fieldset)
    except WrongKeysError as e:
        assert 'x' in str(e)
    try:
        parse_input({'a': 1, 'x':2, 'b':2}, Fieldset)
    except WrongKeysError as e:
        assert 'x' in str(e)
    try:
        parse_input({'a': 1, }, Fieldset)
    except WrongKeysError as e:
        assert 'b' in str(e)

    e = WrongKeysError(missing={'a'}, unknown={'x'}, valid={'a', 'b'})
    assert 'x' in str(e)


def test_enum_error():
    e = str(NotAnEnumItemError('FIELD3', E))
    assert 'FIELD1' in e


def test_correct_items():
    try:
        parse_input([1, 'x', 2], List[int])
    except WrongListItemError as e:
        assert e.wrong_index == 1

    try:
        parse_input({'a': 1, 'b': 'x'}, Mapping[str, int])
    except WrongFieldError as e:
        assert e.wrong_field == 'b'

    try:
        parse_input({1: 2, 'a': 1}, Mapping[str, int])
    except WrongFieldError as e:
        assert e.wrong_field == 1

    try:
        parse_input({'a': 'uno', 'b': 2}, Fieldset)
    except WrongFieldError as e:
        assert e.wrong_field == 'a'
