.. _inout:

Input and output
================

.. testsetup::

    import typing

    import validobj



:py:func:`validobj.validation.parse_input` takes an input to be processed and
andoutput specification. The useful values for these options and the
transformations that result are described below.

Supported input
---------------

Validobj is tested for input that can be processed from JSON. This includes:

* Integers and floats
* Strings
* Booleans
* None
* Lists
* Mappings with string keys (although in practice any hashable key should work)

Other "scalar" types, such as datetimes processed from YAML should work fine.
However these have no tests and no effort is made to avoid corner cases for
more general inputs.

Supported output
----------------

The above is concerted into a wider set of Python objects with additional
restrictions on the type, supported by the typing module.

Simple verbatim input
^^^^^^^^^^^^^^^^^^^^^

All of the above input is supported verbatim

.. doctest::

    >>> validobj.parse_input({'a': 4, 'b': [1,2,"tres", None]}, dict)
    {'a': 4, 'b': [1, 2, 'tres', None]}

Following :py:mod:`typing`, ``type(None)`` can be simply written as ``None``.

.. doctest::

    >>> validobj.parse_input(None, None)

Collections
^^^^^^^^^^^

Lists can be automatically converted to tuples, sets or frozensets.

.. doctest::

    >>> validobj.parse_input([1,2,3],  frozenset)
    frozenset({1, 2, 3})

as well as typed version of the above:

.. doctest::

    >>> import typing
    >>> validobj.parse_input([1,2,3],  typing.FrozenSet[int])
    frozenset({1, 2, 3})
    >>> validobj.parse_input([1,2,'x'],  typing.FrozenSet[int]) #doctest: +SKIP
    Traceback (most recent call last):
    ...
    validobj.errors.WrongTypeError: Expecting value of type 'int', not str.

    The above exception was the direct cause of the following exception:

    Traceback (most recent call last):
    ...
    validobj.errors.WrongListItemError: Cannot process list item 3.


The types of the elements of a tuple can be specified either for each element or
made homogeneous:

.. doctest::

    >>> validobj.parse_input([1,2,'x'],  typing.Tuple[int, int, str])
    (1, 2, 'x')
    >>> validobj.parse_input([1,2,3],  typing.Tuple[int, ...])
    (1, 2, 3)
    >>> validobj.parse_input([1,2,'x'],  typing.Tuple[int, int])
    Traceback (most recent call last):
    ...
    validobj.errors.ValidationError: Expecting value of length 2, not 3
    >>> validobj.parse_input([1,2,3, 'x'],  typing.Tuple[int, ...]) #doctest: +SKIP
    Traceback (most recent call last):
    ...
    validobj.errors.WrongTypeError: Expecting value of type 'int', not str.

    The above exception was the direct cause of the following exception:

    Traceback (most recent call last):
    ...
    validobj.errors.WrongListItemError: Cannot process list item 4.

Unions
^^^^^^

:py:class:`typing.Union` and :py:class:`typing.Optional` are supported:

.. doctest::

    >>> validobj.parse_input("Hello Zah", typing.Union[str, int] )
    'Hello Zah'

    >>> validobj.parse_input([None, 6],  typing.Tuple[typing.Optional[str], int])
    (None, 6)

If a given input can be coerced into more than one of the member of the union, then the order matters:

.. doctest::

    >>> validobj.parse_input([1,2,3], typing.Union[tuple, set])
    (1, 2, 3)
    >>> validobj.parse_input([1,2,3], typing.Union[set, tuple])
    {1, 2, 3}


Any
^^^

:py:class:`typing.Any` is a no-op:


.. doctest::

    >>> validobj.parse_input('Hello', typing.Any)
    'Hello'

Typed mappings
^^^^^^^^^^^^^^


The types of keys and values can be restricted:

.. doctest::

    >>> validobj.parse_input({'key': 'value', 'quantity': 5}, typing.Mapping[str, typing.Union[str, int]])
    {'key': 'value', 'quantity': 5}
    >>> validobj.parse_input({'key': 'value', 'quantity': 5}, typing.Mapping[str, str]) #doctest: +SKIP
    Traceback (most recent call last):
    ...
    validobj.errors.WrongTypeError: Expecting value of type 'str', not int.

    The above exception was the direct cause of the following exception:

    Traceback (most recent call last):
    ...
    validobj.errors.WrongFieldError: Cannot process value for key 'quantity'

Enums
^^^^^

Strings can be automatically converted to valid :py:class:`enum.Enum` elements:

.. doctest::

    >>> import enum
    >>> class Colors(enum.Enum):
    ...     RED = enum.auto()
    ...     GREEN = enum.auto()
    ...     BLUE = enum.auto()
    ... 
    >>> validobj.parse_input('RED', Colors)
    <Colors.RED: 1>
    >>> validobj.parse_input('NORED', Colors) #doctest: +SKIP
    Traceback (most recent call last):
    ...
    validobj.errors.NotAnEnumItemError: 'NORED' is not a valid member of 'Colors'. Alternatives to invalid value 'NORED' include:
      - RED
    All valid values are:
      - RED
      - GREEN
      - BLUE

Additionally lists of strings can be turned into instances of
:py:class:`enum.Flag`:

.. doctest::

    >>> class Permissions(enum.Flag):
    ...     READ = enum.auto()
    ...     WRITE = enum.auto()
    ...     EXECUTE = enum.auto()
    ... 
    >>> validobj.parse_input('READ', Permissions)
    <Permissions.READ: 1>
    >>> validobj.parse_input(['READ', 'EXECUTE'], Permissions)
    <Permissions.EXECUTE|READ: 5>
    >>> validobj.parse_input([], Permissions)
    <Permissions.0: 0>

Dataclasses
^^^^^^^^^^^

The :py:mod:`dataclasses` module supported and input is parsed based on the type annotations:

.. doctest::

    >>> import dataclasses
    >>> @dataclasses.dataclass
    ... class FileMeta:
    ...     description: str = ""
    ...     keywords: typing.List[str] = dataclasses.field(default_factory=list)
    ...     author: str = ""
    >>> @dataclasses.dataclass
    ... class File:
    ...     location: str
    ...     meta: FileMeta = dataclasses.field(default_factory=FileMeta)
    >>> validobj.parse_input({'location': 'https://example.com/file'}, File)
    File(location='https://example.com/file', meta=FileMeta(description='', keywords=[], author=''))

Fields with defaults (or default factories) are inferred. Fields that are
themselves dataclasses are processed recursively.


Rich tracebacks are produced in case of validation error:

.. doctest::

    >>> validobj.parse_input({'location': 'https://example.com/file', 'meta':{'keywords': [1, 'x', 'xx']}}, File) #doctest: +SKIP
    Traceback (most recent call last):
    ...
    validobj.errors.WrongTypeError: Expecting value of type 'str', not int.

    The above exception was the direct cause of the following exception:

    Traceback (most recent call last):
    ...
    validobj.errors.WrongListItemError: Cannot process list item 1.

    The above exception was the direct cause of the following exception:

    Traceback (most recent call last):
    ...
    validobj.errors.WrongFieldError: Cannot process field 'keywords' of value into the corresponding field of 'FileMeta'

    The above exception was the direct cause of the following exception:

    Traceback (most recent call last):
    ...
    validobj.errors.WrongFieldError: Cannot process field 'meta' of value into the corresponding field of 'File'
