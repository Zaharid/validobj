.. _custom:

Defining custom parsers
=======================

.. testsetup::

    import typing

    import validobj



Validobj provides a mechanism to allow supplementing the predefined processing
logic, by annotating types with functions that are invoked to validate the input.

.. note::

    The custom module :py:class:`typing.Annotated` under the hood, so the
    resulting annotations might be processed by static type checkers. Because of
    that, it works only with Python 3.9 onwards.

Custom parsers are created by wrapping a properly annotated validation function with
:py:func:`validobj.custom.Parser`:


1. Define a function with one input with the processing logic. For example::

        import typing
        import decimal

        from validobj import parse_input, ValidationError

        def to_decimal(inp):
            try:
                return decimal.Decimal(inp)
            except decimal.InvalidOperation as e:
                raise ValidationError("Invalid decimal") from e

 The custom function should raise an instance of
 :py:class:`validobj.errors.ValidationError` to indicate validation failure.
 Other exceptions will be treated as programming errors.

2. Add type annotations to the input parameter and return type::

        def to_decimal(inp: str|float]) -> decimal.Decimal:
            ...

 The Validobj :ref:`logic <inout>` is used to cast the input into the type
 annotated in the input parameter. The custom function will only be called if
 the cast succeeds. The return annotation of the custom function is not checked
 or enforced by Validobj, but might be useful for static type checkers.

3. Wrap the function with :py:func:`validobj.custom.Parser` to create a type annotation::

        MyDecimal = Parser(to_decimal)

 ``MyDecimal`` can be used whenever we want to use Validobj obtain a decimal from a string or a number.

4. Use the type annotation with Validobj::

        >>> parse_input(0.5, MyDecimal)
        Decimal('0.5')


The validators can also be create as closures:

.. doctest::
    :pyversion: >= 3.9

    >>> from validobj.custom import Parser
    >>> from validobj import parse_input, ValidationError
    >>> def make_range(a, b):
    ...     def parser(n: float) -> float:
    ...         if not a <= n < b:
    ...             raise ValidationError(f"Expecting {a} <= n < {b}, but n={n}")
    ...         return n
    ...     return parser
    ... 
    >>> RangeFloat = Parser(make_range(0, 10))
    >>> parse_input(3.14, RangeFloat)
    3.14
    >>> parse_input(-0.1, RangeFloat) #doctest: +SKIP
    Traceback (most recent call last):
    ...
    ValidationError: Expecting 0 <= n < 10, but n=-0.1


The custom logic can be used to add restrictions on the input to some existing
type, while taking advantage of the fact that the input is already processed
into that type.

.. doctest::
    :pyversion: >= 3.9

    >>> import dataclasses
    >>> @dataclasses.dataclass
    ... class Point:
    ...     x: float
    ...     y: float
    ... 
    >>> def in_unit_circle_point(p: Point) -> Point:
    ...     if not p.x**2 + p.y**2 < 1:
    ...         raise ValidationError("Point outside unit circle")
    ...     return p
    ... 
    >>> UnitCirclePoint = Parser(in_unit_circle_point)
    >>> parse_input({"x": 0.4, "y": 0.2}, UnitCirclePoint)
    Point(x=0.4, y=0.2)
    >>> parse_input({"x": 0.4, "y": "ups"}, UnitCirclePoint) #doctest: +SKIP
    Traceback (most recent call last):
    ...
    WrongFieldError: Cannot process field 'y' of value into the corresponding field of 'Point'
    >>> parse_input({"x": 0.4, "y": 0.98}, UnitCirclePoint) #doctest: +SKIP
    Traceback (most recent call last):
    ...
    ValidationError: Point outside unit circle


:py:func:`validobj.custom.Parser` 
While the result of :py:func:`validobj.custom.Parser` is an annotation
compatible with static type checkers. Specifically::

    typing.Annotated[
        <return type>,
        validobj.custom.InputType(
            <input type of parameter>
        ),
        validobj.custom.Validator(
            <function>
        )
    ]

That is, the two metadata parameters
accompanying the type of the processed object should be the type of the input
wrapped in :py:class:`validobj.custom.InputType` and the function doing the
validation, wrapped in :py:class:`validobj.custom.Validator`.

.. doctest::
    :pyversion: >= 3.9

    >>> from validobj.custom import InputType, Validator
    >>> UnitCirclePoint = typing.Annotated[Point, InputType(Point), Validator(in_unit_circle_point)]
    >>> parse_input({"x": 0.4, "y": 0.5}, UnitCirclePoint)
    Point(x=0.4, y=0.5)
