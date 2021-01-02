"""
The validation module implements the :py:func:`parse_input` function.


.. testsetup::

    import typing

    import validobj


"""
from typing import Set, Union, Any, Optional, TypeVar, Type
from types import FunctionType
from collections.abc import Mapping
import dataclasses
import enum

from validobj.errors import (
    ValidationError,
    UnionValidationError,
    WrongTypeError,
    WrongKeysError,
    NotAnEnumItemError,
    WrongFieldError,
    WrongListItemError,
)

__all__ = ('parse_input',)


def _match_sets(
    provided: Set,
    required: Optional[Set] = None,
    allowed: Optional[Set] = None,
    header: Optional[str] = None,
):
    missing = required - provided if required else set()
    unknown = provided - allowed if allowed else set()
    if missing or unknown:
        raise WrongKeysError(missing, unknown, allowed, header)


def _parse_std_list_collection(value, spec):
    if not isinstance(value, list):
        raise WrongTypeError(
            f"Expecting value to be a list, not {_typename(type(value))}"
        )
    try:
        return spec(value)
    # Unhashable types
    except TypeError as e:
        raise WrongTypeError(
            f"Cannot convert input list to type {_typename(spec)}: {e}"
        ) from e


def _typename(tp):
    if hasattr(tp, '__name__'):
        return tp.__name__
    return str(tp)


def _sane_typing_args(tp):
    if isinstance(tp, tuple) and len(tp) == 1 and isinstance(tp[0], TypeVar):
        return Any
    return tp


def _parse_homogeneous_typying_collection(value, origin, inner):
    if not isinstance(value, list):
        raise WrongTypeError(
            f"Expecting value to be a list, not {_typename(type(value))}"
        )
    res = []
    for i, item in enumerate(value):
        try:
            res.append(parse_input(item, inner))
        except ValidationError as e:
            raise WrongListItemError(
                f"Cannot process list item {i+1}.", wrong_index=i
            ) from e
    return origin(res)


def _parse_typying_tuple(value, inner):
    if not isinstance(value, list):
        raise WrongTypeError(
            f"Expecting value to be a list, not {_typename(type((value)))}"
        )

    if len(value) != len(inner):
        raise ValidationError(
            f"Expecting value of length {len(inner)}, not {len(value)}"
        )

    res = []
    for i, (item, tp) in enumerate(zip(value, inner), 1):
        try:
            res.append(parse_input(item, tp))
        except ValidationError as e:
            raise WrongListItemError(f"Cannot process item {i}.", wrong_index=i) from e
    return tuple(res)


def _parse_typing_mapping(value, spec):
    if not isinstance(value, dict):
        raise WrongTypeError(
            f"Expecting value to ve a dict, not {_typename(type(value))!r}"
        )
    res = {}
    key_tp = _sane_typing_args(spec.__args__[0])
    value_tp = _sane_typing_args(spec.__args__[1])
    for k, v in value.items():
        try:
            parsed_k = parse_input(k, key_tp)
        except ValidationError as e:
            raise WrongFieldError(f"Cannot process mapping key", wrong_field=k) from e

        try:
            parsed_v = parse_input(v, value_tp)
        except ValidationError as e:
            raise WrongFieldError(
                f"Cannot process value for key {parsed_k!r}", wrong_field=k
            ) from e
        res[parsed_k] = parsed_v
    return res


def _dataclass_required_allowed(cls):
    allowed = set()
    required = set()
    for field in dataclasses.fields(cls):
        name = field.name
        allowed.add(name)
        if (
            field.default is dataclasses.MISSING
            and field.default_factory is dataclasses.MISSING
        ):
            required.add(name)
    return required, allowed


def _parse_dataclass(value, spec):
    if not isinstance(value, dict):
        raise WrongTypeError(
            f"Expecting value to be a dict, compatible with {_typename(spec)!r}, "
            f"not {_typename(type(value))!r}"
        )
    _match_sets(
        value.keys(),
        *_dataclass_required_allowed(spec),
        header=f"Cannot process value into {_typename(spec)!r} because "
        f"fields do not match.",
    )
    res = {}
    field_dict = {f.name: f.type for f in dataclasses.fields(spec)}
    for k, v in value.items():
        try:
            res[k] = parse_input(v, field_dict[k])
        except ValidationError as e:
            raise WrongFieldError(
                f"Cannot process field {k!r} of value into the "
                f"corresponding field of {_typename(spec)!r}",
                wrong_field=k,
            ) from e
    return spec(**res)


def _parse_single_enum(value, spec):
    if not isinstance(value, str):
        raise WrongTypeError(
            f"Expecting value to be a string, not {_typename(type(value))!r}"
        )
    if not value in spec.__members__:
        raise NotAnEnumItemError(value, spec)
    return spec.__members__[value]


def _parse_list_enum(value, spec):
    # This is a hidden function to create an enum composition with no members
    res = spec._create_pseudo_member_(0)
    for i, item in enumerate(value):
        try:
            res |= _parse_single_enum(item, spec)
        except ValidationError as e:
            raise WrongListItemError(
                f"Cannot process item {i+1} into {_typename(spec)!r}.", wrong_index=i
            ) from e
    return res


def _parse_enum(value, spec):
    if isinstance(value, list) and issubclass(spec, enum.Flag):
        return _parse_list_enum(value, spec)
    return _parse_single_enum(value, spec)


def _handle_typing_spec(value, spec):
    if not hasattr(spec, '__args__'):
        return parse_input(value, spec.__origin__)
    if spec.__origin__ in (list, set, frozenset):
        inner = _sane_typing_args(spec.__args__)
        return _parse_homogeneous_typying_collection(value, spec.__origin__, inner)
    if spec.__origin__ is tuple:
        if len(spec.__args__) == 2 and spec.__args__[1] is Ellipsis:
            inner = _sane_typing_args(spec.__args__[0])
            return _parse_homogeneous_typying_collection(value, spec.__origin__, inner)
        else:
            return _parse_typying_tuple(value, spec.__args__)
    elif spec.__origin__ in (Mapping, dict):
        return _parse_typing_mapping(value, spec)
    elif spec.__origin__ is Union:
        tp = _sane_typing_args(spec.__args__)
        return parse_input(value, tp)
    else:
        raise NotImplementedError(f"Validation not implemented for {spec}")


T = TypeVar("T")


def parse_input(value: Any, spec: Type[T]) -> T:
    """
    This is the main entry point of the validobj module.
    Validates and processes the input value based on the provided
    specification.


    Parameters
    ----------
    value : Any
        The value to be processed.
    spec : :py:class:`type` or :py:mod:`typing` specification
        The target specification.

    Returns
    -------
    value : Any, compatible with ``spec``
        The processed form of value. This can be the input value
        itself if only a (recursive) type check was performed
        or a more structured output, based on the type of the
        specification.

    Raises
    ------
    ValidationError
        Raised if the input cannot be coerced to the spec. An
        appropriate subclass defined in :py:mod:`validobj.errors`
        will contain more specific information as well ``__cause__``
        fields chained as neccessary.

    Notes
    -----
    The parameters are described in detail in :ref:`Input and output <inout>`.

    The error handling is described in :ref:`Errors <errors>`.

    Examples
    --------

    Check that a given input is a mapping of string to integer:

    .. doctest::

        >>> validobj.parse_input({'key1': 1, 'key2': 2}, typing.Mapping[str, int])
        {'key1': 1, 'key2': 2}

    Coerce the input to a dataclass of a valid shape:

    .. doctest::

        >>> import dataclasses
        >>> @dataclasses.dataclass
        ... class Data:
        ...     key: str
        ...     key2: int = 4
        ... 
        >>> validobj.parse_input({'key': 'Hello'}, Data)
        Data(key='Hello', key2=4)

    Find a list item that does not conform to the specification:

    .. doctest::

        >>> import typing
        >>> try:
        ...    validobj.parse_input([1,2,'tres'], typing.List[int])
        ... except validobj.ValidationError as e:
        ...    e.wrong_index
        ... 
        2

    """
    if spec is dataclasses.MISSING or spec is Any:
        return value
    # None is a special calse, as specified in
    # https://docs.python.org/3/library/typing.html#type-aliases
    if spec is None:
        return parse_input(value, type(None))
    if isinstance(spec, tuple):
        # Remove one level of exceptions
        if len(spec) == 1:
            return parse_input(value, spec[0])
        error_strings = []
        causes = []
        for tp in spec:
            try:
                return parse_input(value, tp)
            except ValidationError as e:
                error_strings.append(f"Not a valid match for {_typename(tp)!r}: {e}")
                exc = e
                causes.append(exc)
                continue
        all_errors = '\n'.join(error_strings)
        raise UnionValidationError(
            f"No match for any possible type:\n{all_errors}", causes=causes
        )
    if spec in {tuple, set, frozenset}:
        return _parse_std_list_collection(value, spec)

    if isinstance(spec, type) and issubclass(spec, enum.Enum):
        return _parse_enum(value, spec)
    if dataclasses.is_dataclass(spec):
        return _parse_dataclass(value, spec)

    if hasattr(spec, '__origin__'):
        return _handle_typing_spec(value, spec)

    # Handle typing.NewType
    if isinstance(spec, FunctionType) and hasattr(spec, '__supertype__'):
        # Don't use __name__ in the error because we want the input type
        tp = spec.__supertype__
    else:
        tp = spec

    if isinstance(value, tp):
        return value
    else:
        raise WrongTypeError(
            f"Expecting value of type {_typename(tp)!r}, not {_typename(type(value))}."
        )
