.. _errors:

.. testsetup::

    import validobj

Error handling
==============

Validobj aims to be good at providing good error messages by default, and
enough metadata so that errors can be repurposed or improved. That metadata is
enough to for example attach YAML line numbers to the sources of error.

Generic errors
--------------

All exceptions raised by Validobj are subclasses of
:py:class:`validobj.errors.ValidationError`. Therefore it can be used in an
``except`` block to tell if the validation succeeded.

.. doctest::


    >>> try:
    ...     result = validobj.parse_input([1, 2, "3"], list)
    ... except validobj.ValidationError as e:
    ...     print("Validation failed")
    ... else:
    ...     print("Validation succeeded")
    ...
    Validation succeeded

Errors for Unions
-----------------

Errors for union types (including :py:class:`typing.Optional`) result in a
:py:class:`validobj.errors.UnionValidationError` being raised. The exception
contains a ``causes`` attribute containing the reasons for the mismatch for
each of the individual types.

.. doctest::

    >>> from typing import Optional, List
    >>> validobj.parse_input([1, "dos"], Optional[List[int]])
    Traceback (most recent call last):
    ...
    UnionValidationError: No match for any possible type:
    Not a valid match for 'typing.List[int]': Cannot process list item 2.
    Not a valid match for 'NoneType': Expecting value of type 'NoneType', not list.


Key mismatch
-------------

The optional and required keys in a mapping can be specified through the
definition of a dataclass. For example:

.. testcode::

    import dataclasses
    from typing import Optional, List


    @dataclasses.dataclass
    class User:
        name: str
        phone: Optional[str] = None
        tasks: List[str] = dataclasses.field(default_factory=list)

means that the class ``User`` has one required field, ``name`` (because it
doesn't have a default) and two optional fields, ``phone`` and ``tasks``
(because they have a simple value default and a default factory respectively).

When provided values do not match the specification, either because unknown
keys are provided or required keys are missing, a
:py:class:`validobj.errors.WrongKeysError` is raised. The error knows about
unknown, missing and valid keys and stores them in as the ``unkown``,
``missing`` and ``valid`` attributes respectively. Suggestions will be given
for invalid keys that look like typos.

.. doctest::

    >>> validobj.parse_input({
    ...      'phone': '555-1337-000', 'address': 'Somewhereville', 'nme': 'Zahari'}, User
    ... )
    Traceback (most recent call last):
    ...
    WrongKeysError: Cannot process value into 'User' because fields do not match.
    The following required keys are missing: {'name'}. The following keys are unknown: {'nme', 'address'}.
    Alternatives to invalid value 'nme' include:
      - name

    All valid options are:
      - name
      - phone
      - tasks

The attributes of the exception can be inspected:

.. doctest::

    >>> from validobj.errors import WrongKeysError
    >>> try:
    ...     validobj.parse_input({'phone': '555-1337-000',
    ...         'address': 'Somewhereville', 'nme': 'Zahari'},
    ...     User)
    ... except WrongKeysError as e:
    ...     print(f'The missing keys are  {sorted(e.missing)!r}')
    ...
    The missing keys are  ['name']



Wrong keys
----------

When a given value in a mapping fails to be processed, the original exception
is wrapped with a :py:class:`validobj.errors.WrongFieldError` so that it is its
``__cause__``. The problematic field is stored in the ``wrong_field`` attribute:

.. doctest::

    >>> validobj.parse_input({'name': 11}, User) #doctest: +SKIP
    Traceback (most recent call last):
    ...
    WrongTypeError: Expecting value of type 'str', not int.

    The above exception was the direct cause of the following exception:
    ...
    WrongFieldError: Cannot process field 'name' of value into the corresponding field of 'User'


Wrong list items
----------------

Analogously to mapping keys, when a given list item fails to
conform to the specification, a :py:class:`validobj.errors.WrongListItemError`
is raised. The problematic index is stored in the ``wrong_index`` attribute of
the exception. The original error is stored as the ``__cause__``.

.. doctest::

    >>> validobj.parse_input([{'name': "Eleven"}, {'name': 11}], List[User]) # doctest: +SKIP
    Traceback (most recent call last):
        ...
    WrongTypeError: Expecting value of type 'str', not int.
        ...
    The above exception was the direct cause of the following exception:
        ...
    Traceback (most recent call last):
        ...
    WrongFieldError: Cannot process field 'name' of value into the corresponding field of 'User'
        ...
    The above exception was the direct cause of the following exception:
        ...
    Traceback (most recent call last):
         ...
    WrongListItemError: Cannot process list item 2.


Note that there are as many levels of chaining as  necessary.

Wrong enum elements
-------------------

Wrong enum elements will result in a
:py:class:`validobj.errors.NotAnEnumItemError`. These errors know about the
original enum class and  will suggest fixes to the typos. Additionally
:py:class:`enum.Flag` combinations will behave like lists and raise a
:py:class:`validobj.errors.WrongListItemError`.

.. doctest::

    >>> import enum
    >>> import validobj
    >>> class DiskPermissions(enum.Flag):
    ...     READ = enum.auto()
    ...     WRITE = enum.auto()
    ...     EXECUTE = enum.auto()
    ...
    >>> validobj.parse_input(['EXECUTE', 'RAED'], DiskPermissions) # doctest: +SKIP
    NotAnEnumItemError                        Traceback (most recent call last)
    ...
    NotAnEnumItemError: 'RAED' is not a valid member of 'DiskPermissions'.
    Alternatives to invalid value 'RAED' include:
      - READ
    All valid values are:
      - READ
      - WRITE
      - EXECUTE

    The above exception was the direct cause of the following exception:
    ...
    WrongListItemError: Cannot process item 2 into 'DiskPermissions'.
