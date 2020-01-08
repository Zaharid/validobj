Examples
========

.. testsetup::

    from autoparse_decorator import autoparse
    from autoparse_usage import check_transfer

Function decorator
------------------

Validobj can be used in a function decorator to automatically validate each
function argument based on its type annotation. The code to achieve is:

.. literalinclude:: ../examples/autoparse_decorator.py

The functions decorated with ``autoparse`` take simple input and use
:py:func:`validobj.validation.parse_input` to make it conform to the type
specification.

.. doctest::

    >>> import enum
    >>> class Currency(enum.Enum):
    ...     EUR = 0.01
    ...     GBP = 0.018
    ...
    >>> @autoparse
    ... def print_funds_in_euro(quantity_cents: int, currency: Currency):
    ...     print(f"{quantity_cents*currency.value:.2f} {Currency.EUR.name}")
    >>> print_funds_in_euro(4, 'GBP')
    0.07 EUR

This can be useful to perform application specific validation that cannot be
easily encoded in types. For example we may want to check if a given account
exists and has enough funds to perform a transfer:

.. literalinclude:: ../examples/autoparse_usage.py

Then the usage is:

.. doctest::

    >>> check_transfer({'origin': 'Bob', 'destination': 'Alice', 'quantity': 100})
    Transfer(origin='Bob', destination='Alice', quantity=100)
    >>> check_transfer({'origin': 'Bob', 'destination': 'Alice', 'quantity': 400})
    Traceback (most recent call last):
        ...
    WrongFieldError: Insufficient funds


YAML line numbers
-----------------

The :ref:`errors <errors>` in Validobj provide enough information to associate
the line number with the cause of the error, when combined with a library that
tracks the line information such as `ruamel.yaml
<https://bitbucket.org/ruamel/yaml/src/default/>`_. It is possible to climb up
the ``__cause__`` of the errors to produce a detailed traceback. The following code achieves that:


.. literalinclude:: ../examples/yaml_processing.py

An example usage is:


.. literalinclude:: ../examples/yaml_lines_usage.py

Which prints:

.. code-block::


    Problem processing key at line 2:
    Cannot process field 'stages' of value into the corresponding field of 'CIConf'
    Problem processing list item at line 6:
    Cannot process list item 2.
    Unknown key 'script' defined at line 8:
    Cannot process value into 'Job' because fields do not match.
    The following required keys are missing: {'script_path'}. The following keys are unknown: {'script'}.
    Alternatives to invalid value 'script' include:
      - script_path
    All valid options are:
      - disk_permissions
      - framework_version
      - name
      - os
      - script_path
