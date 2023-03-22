"""Tools for :ref:`custom validation <custom>` of types.
Works with Python 3.9 only.

.. testsetup::

    import typing

    from validobj.custom import Parser

"""
from typing import Annotated, Any, Type, Callable, TypeVar
import functools
import inspect


__all__ = ["InputType", "Validator", "Parser"]


class InputType:
    """A wrapper over an input type, for use in the  :ref:`custom <custom>` processing.

    Parameters
    ----------
    type : Type
        The wrapped type.
    """

    def __init__(self, type: Type):
        self.type = type

    def __repr__(self):
        return f'{self.__class__.__name__}({repr(self.type)})'


class Validator:
    """A wrapper over a validation function, for use in the  :ref:`custom <custom>`
    processing.

    Parameters
    ----------
    func : Callable
        The wrapped function.
    """

    def __init__(self, func: Callable):
        self.func = func
        functools.update_wrapper(self, func)

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def __repr__(self):
        return f'{self.__class__.__name__}({repr(self.func)})'


T = TypeVar("T")

def Parser(func: Callable[[Any], T]) -> Type[T]:
    """
    Read the type annotations of ``func`` and return a
    :py:class:`typing.Annotated` with the function's return type as the set
    type and the requisite metadata so that ``func`` is used by
    :py:func:`validobj.parse_input`.


    Parameters
    ----------
    func : Callable
        The wrapped function. It should have one positional parameter. If the
        parameter is annotated, Validobj will cast the input consitently with
        the annotation before presenting it to the function.

    Returns
    -------
    annotated : :py:data:`typing._AnnotatedAlias`
        Annotation of the return type of the function with two metadata parameters:
        :py:class:`InputType` with the type annotation of the first parameter and
        :py:class:`Validator` with the function itself.


    Examples
    --------

    Add support for :py:class:`decimal.Decimal`.

    .. doctest::
        :pyversion: >= 3.9

        >>> import typing
        >>> import decimal
        >>> from validobj import parse_input, ValidationError
        >>> from validobj.custom import Parser
        >>> def to_decimal(inp: typing.Union[str, int, float]) -> decimal.Decimal:
        ...     try:
        ...         return decimal.Decimal(inp)
        ...     except decimal.InvalidOperation as e:
        ...         raise ValidationError("Invalid decimal") from e
        ...
        >>> Decimal = Parser(to_decimal)
        >>> print(Decimal)
        typing.Annotated[decimal.Decimal, InputType(typing.Union[str, int, float]), Validator(<function to_decimal at ...>)]
        >>> parse_input(0.5, Decimal)
        Decimal('0.5')
    """
    s = inspect.signature(func)
    if not s.parameters:
        raise ValueError("Expecting at least one parameter")
    ret = s.return_annotation
    if ret is s.empty:
        ret = Any

    p = next(iter(s.parameters.values()))
    inp = p.annotation
    if inp is s.empty:
        inp = Any
    return Annotated[ret, InputType(inp), Validator(func)]
