Welcome to Validobj's documentation!
====================================


Validobj is a library that processes semistructured input coming from sources a
JSON mapping or a YAML configuration file  into more structured Python objects.
The main API function, :py:func:`validobj.validation.parse_input`, takes care
of that

.. literalinclude:: ../examples/basic.py

The full set of applied checks and transformations is described in :ref:`Input
and output <inout>`.


Validobj aims at providing building blocks to construct the most human friendly
error handling in town. Its exceptions provide lots of information on what went
wrong as well as good messages, which even contain suggestions on typos.

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

When more control is needed, Validobj allows :ref:`passing custom functions to
handle transformations <custom>`.


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   inout
   errors
   custom
   examples
   apisrc/modules




Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
