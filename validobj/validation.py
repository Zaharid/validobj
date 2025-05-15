"""
The validation module implements the :py:func:`parse_input` function.


.. testsetup::

    import typing

    import validobj


"""
from typing import Set, Union, Any, Optional, TypeVar, Type, Literal
import sys

try:
    from typing import _TypedDictMeta
except ImportError: # pragma: nocover
    HAVE_TYPED_DICT = False
else:
    HAVE_TYPED_DICT = sys.version_info >= (3, 9)

try:
    from typing import _AnnotatedAlias
except ImportError: # pragma: nocover
    HAVE_ANNOTATED = False
else:
    HAVE_ANNOTATED = True
    from validobj.custom import InputType, Validator

try:
    from typing import TypeAliasType
except ImportError:  # pragma: nocover
    HAVE_TYPE_ALIAS = False
else:
    HAVE_TYPE_ALIAS = True

try:
    from types import UnionType
except ImportError: # pragma: nocover
    HAVE_UNION_TYPE = False
else:
    HAVE_UNION_TYPE = True

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
    WrongLiteralError,
)

__all__ = [
    'parse_input',
]


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


def _dataclasses_fields(class_or_instance):
    """
    A copy of dataclasses.fields that also returns InitVar fields.
    """

    # Might it be worth caching this, per class?
    try:
        fields = getattr(class_or_instance, dataclasses._FIELDS)
    # We should not be calling this function with anything other than dataclasses.
    except AttributeError: # pragma: nocover
        raise TypeError('must be called with a dataclass type or instance')

    # Exclude pseudo-fields.  Note that fields is sorted by insertion
    # order, so the order of the tuple is as the fields were defined.
    return tuple(
        f
        for f in fields.values()
        if f._field_type is dataclasses._FIELD
        or f._field_type is dataclasses._FIELD_INITVAR
    )


def _dataclass_required_allowed(fields):
    allowed = set()
    required = set()
    for field in fields:
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
    fields = _dataclasses_fields(spec)
    _match_sets(
        value.keys(),
        *_dataclass_required_allowed(fields),
        header=f"Cannot process value into {_typename(spec)!r} because "
        f"fields do not match.",
    )
    res = {}
    field_dict = {
        # Look inside InitVar
        f.name: f.type if not isinstance(f.type, dataclasses.InitVar) else f.type.type
        for f in fields
    }
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


def _parse_typed_dict(value, spec):
    if not isinstance(value, dict):
        raise WrongTypeError(
            f"Expecting value to be a dict, not {_typename(type(value))}"
        )
    _match_sets(
        value.keys(),
        spec.__required_keys__,
        spec.__required_keys__ | spec.__optional_keys__,
        header=f"Cannot process value into {_typename(spec)!r} because "
        f"fields do not match.",
    )
    res = {}
    for k, v in value.items():
        try:
            res[k] = parse_input(v, spec.__annotations__[k])
        except ValidationError as e:
            raise WrongFieldError(
                f"Cannot process field {k!r} of value into the "
                f"corresponding field of {_typename(spec)!r}",
                wrong_field=k,
            ) from e
    return res


def _parse_namedtuple(value, spec):
    if not isinstance(value, list):
        raise WrongTypeError(
            f"Expecting value to be a list, not {_typename(type(value))}"
        )


    if len(value) > len(spec._fields):
        raise ValidationError(
            f"Expecting value of length at most {len(spec._fields)}, not {len(value)}"
        )

    required = set(spec._fields) - spec._field_defaults.keys()
    field_inputs = dict(zip(spec._fields, value))

    _match_sets(
        field_inputs.keys(),
        required,
        spec._fields,
        header=f"Cannot process value into {_typename(spec)!r} because "
        f"insufficient items are provided.",
    )

    # Python 3.9: collections.namedtuple does not have __annotations__.
    if not hasattr(spec, '__annotations__'):
        return spec(**field_inputs)

    res = {}

    for i, (k, v) in enumerate(field_inputs.items()):
        if k in spec.__annotations__:
            try:
                res[k] = parse_input(v, spec.__annotations__[k])
            except ValidationError as e:
                raise WrongListItemError(
                    f"Cannot process list item {i+1} into the field {k!r} of {_typename(spec)!r}",
                    wrong_index=i,
                ) from e
        else:
            res[k] = v

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
    res = spec(0)
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


def _parse_annotated(value, spec):
    meta = spec.__metadata__
    if len(meta) == 2 and isinstance(meta[0], InputType) and isinstance(meta[1], Validator):
        inp, func = meta
        parsed = parse_input(value, inp.type)
        return func(parsed)
    return parse_input(value, spec.__origin__)


def _reduce_literal_args(args):
    l = []
    for arg in args:
        if getattr(arg, '__origin__', None) is Literal:
            l.extend(_reduce_literal_args(arg.__args__))
        else:
            l.append(arg)
    return l


def _parse_literal(value, references):
    for reference in references:
        if type(value) == type(reference) and value == reference:
            return value
    raise WrongLiteralError(value, references)

def _handle_union(value, args):
    tp = _sane_typing_args(args)
    return parse_input(value, tp)

def _handle_typing_spec(value, spec):
    if not hasattr(spec, '__args__'):  # pragma: nocover
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
        return _handle_union(value, spec.__args__)
    elif spec.__origin__ is Literal:
        return _parse_literal(value, _reduce_literal_args(spec.__args__))
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
    # None is a special case, as specified in
    # https://docs.python.org/3/library/typing.html#type-aliases
    if spec is None:
        return parse_input(value, type(None))
    if HAVE_TYPE_ALIAS and isinstance(spec, TypeAliasType):
        return parse_input(value, spec.__value__)
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

    if spec is float and isinstance(value, int):
        return float(value)

    if spec is complex and isinstance(value, (int, float)):
        return complex(value)

    if spec in {tuple, set, frozenset}:
        return _parse_std_list_collection(value, spec)

    # Namedtuple
    if isinstance(spec, type) and issubclass(spec, tuple) and hasattr(spec, '_fields'):
        return _parse_namedtuple(value, spec)

    if isinstance(spec, type) and issubclass(spec, enum.Enum):
        return _parse_enum(value, spec)

    if dataclasses.is_dataclass(spec):
        return _parse_dataclass(value, spec)

    if HAVE_UNION_TYPE and isinstance(spec, UnionType):
        return _handle_union(value, spec.__args__)

    if HAVE_TYPED_DICT and isinstance(spec, _TypedDictMeta):
        return _parse_typed_dict(value, spec)

    if HAVE_ANNOTATED and isinstance(spec, _AnnotatedAlias):
        return _parse_annotated(value, spec)

    if hasattr(spec, '__origin__'):
        return _handle_typing_spec(value, spec)

    # Handle typing.NewType
    if hasattr(spec, '__supertype__'):
        # Don't use __name__ in the error because we want the input type
        return parse_input(value, spec.__supertype__)

    if isinstance(value, spec):
        return value
    else:
        raise WrongTypeError(
            f"Expecting value of type {_typename(spec)!r}, not {_typename(type(value))}."
        )
