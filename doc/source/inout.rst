.. _inout:

Input and output
================

.. testsetup::

    import typing

    import validobj



:py:func:`validobj.validation.parse_input` takes an input raw object, to be
processed, and an output type specification specification to process the object
into.

Supported input
---------------

Validobj is tested for input that can be processed from JSON. This includes:

* Integers and floats
* Strings
* Booleans
* None
* Lists
* Mappings with string keys (although in practice any hashable key should work)

Other "scalar" types, such as datetimes processed from YAML should work fine
(an ``isinstance`` check is performed as a last resort).
However these have no tests and no effort is made to avoid corner cases for
more general inputs. Users can add :ref:`customizations <custom>` for these as
appropriate for their application.

Supported output
----------------

The input is coerced into a wider set of Python objects, as specified by the
target specification.

Simple verbatim input
^^^^^^^^^^^^^^^^^^^^^

All of the above input is supported verbatim

.. doctest::

    >>> validobj.parse_input({'a': 4, 'b': [1, 2, "tres", None]}, dict)
    {'a': 4, 'b': [1, 2, 'tres', None]}

Following :py:mod:`typing`, ``type(None)`` can be simply written as ``None``.

.. doctest::

    >>> validobj.parse_input(None, None)

Also following typing conventions, ``int`` inputs are allowed as floats, but
these will be be cast to ``float``:

.. doctest::

    >>> validobj.parse_input(1, float)
    1.0

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

:py:data:`typing.Union` and :py:data:`typing.Optional` are supported:

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

From Python 3.10, union types can be specified using the ``X | Y`` syntax.

.. doctest::
    :pyversion: >= 3.10

    >>> validobj.parse_input([1,2,3], tuple | set)
    (1, 2, 3)


Literals
^^^^^^^^

:py:data:`typing.Literal` is supported with recent enough versions of the typing module::

    >>> validobj.parse_input(5, typing.Literal[1, 2, typing.Literal[5]])
    5


Annotated
^^^^^^^^^

:py:data:`typing.Annotated` is used to enable :ref:`custom processing <custom>`
of types. Other annotation metadata  is ignored.


.. doctest::
    :pyversion: >= 3.9

    >>> validobj.parse_input(5, typing.Annotated[int, "bogus"])
    5

Any
^^^

:py:data:`typing.Any` is a no-op:


.. doctest::

    >>> validobj.parse_input('Hello', typing.Any)
    'Hello'

Type aliases
^^^^^^^^^^^^

Types can be defined as :py:class:`typing.TypeAliasType`, using the :code:`type`
syntax in Python 3.12 onwards:

.. doctest::
   :pyversion: >= 3.12

    >>> type MyType = str | tuple[str, str]
    >>> validobj.parse_input(["hi", "there"], MyType)
    ('hi', 'there')

NewType
^^^^^^^

:py:class:`typing.NewType` works the same as if the type it wraps was given as
input:

.. doctest::

   >>> MyNewType = typing.NewType("MyNewType", typing.Literal[5, 6])
   >>> validobj.parse_input(5, MyNewType)
   5



Typed mappings
^^^^^^^^^^^^^^

:py:class:`typing.TypedDict` is supported for Python versions newer than 3.9,
including with nesting of types.

.. doctest::
    :pyversion: >= 3.8

    >>> class Config(typing.TypedDict):
    ...     a: str
    ...     b: typing.Optional[typing.List[int]]
    ... 
    >>> validobj.parse_input({"a": "Hello", "b": [1,2,3]}, Config)
    {'a': 'Hello', 'b': [1, 2, 3]}
    >>> validobj.parse_input({"a": "Hello", "b": [1,2,"three"]}, Config) #doctest: +SKIP
    ...
    WrongFieldError: Cannot process field 'b' of value into the corresponding field of 'Config'


:py:class:`typing.Mapping` can be used to restrict types of keys and values, for arbitrary keys;

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

NamedTuple
^^^^^^^^^^

:py:class:`typing.NamedTuple` (as well as the factory
:py:func:`collections.namedtuple`) is supported, including annotations and
default elements. The input to a tuple should be a list rather than a dict.

.. doctest::

    >>> import typing
    >>> class Record(typing.NamedTuple):
    ...     uid: int
    ...     name: str
    ...     address: typing.Optional[str] = None
    >>> validobj.parse_input([1, "Zah"], Record)
    Record(uid=1, name='Zah', address=None)
    >>> validobj.parse_input([1, "Zah", {"Address"}], Record)
    Traceback (most recent call last):
    ...
    WrongListItemError: Cannot process list item 3 into the field 'address' of 'Record'



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
    :pyversion: <= 3.10

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

Note that enums are matched by name rather than by value. This allows for more
natural support of ``enum.auto`` and ``enum.Flag``.

Dataclasses
^^^^^^^^^^^

The :py:mod:`dataclasses` module is supported and input is parsed based on the
type annotations:

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
    ...     storage_class: dataclasses.InitVar[str] = "local"
    >>> validobj.parse_input({'location': 'https://example.com/file', 'storage_class': 'remote'}, File)
    File(location='https://example.com/file', meta=FileMeta(description='', keywords=[], author=''))

Fields with defaults (or default factories) are inferred. Fields that are
themselves dataclasses are processed recursively. Init-only variables using
:py:class:`dataclasses.InitVar` are supported, with the types checked.


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
