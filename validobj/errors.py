"""
The ``errors`` module defines the exceptions raised by
:py:func:`validobj.validation.parse_input` function. These are aleways
subclasses of :py:class:`ValidationError`.
"""

import difflib

__all__ = (
    'ValidationError',
    'WrongTypeError',
    'WrongKeysError',
    'NotAnEnumItemError',
    'WrongFieldError',
    'WrongListItemError',
    'UnionValidationError',
)


def print_list(options):
    return "\n".join(f"  - {a}" for a in options)


class AlternativeDisplay:
    alternatives_suffix = (
        "Alternatives to invalid value {self.bad_item!r}"
        " include:\n{self.alternative_text}"
    )

    def __init__(
        self,
        header='',
        bad_item=None,
        alternatives=None,
        display_all_alternatives=False,
    ):
        self.bad_item = bad_item
        if alternatives:
            alternatives = list(alternatives)
        self.header = header
        self.alternatives = alternatives
        self.display_all_alternatives = display_all_alternatives

    @property
    def _alternative_displayed_options(self):
        if not self.display_all_alternatives:
            return difflib.get_close_matches(self.bad_item, self.alternatives)
        return self.alternatives

    @property
    def alternative_text(self):
        return print_list(self._alternative_displayed_options)

    def __str__(self):
        if not self._alternative_displayed_options:
            return self.header
        return f"{self.header}{self.alternatives_suffix.format(self=self)}"


class ValidationError(Exception):
    """Exception raised when validation cannot be performed for any reason."""


class UnionValidationError(ValidationError):
    """Exception raised when value cannot be coerced to any of the members of
    an union.

    Parameters
    ----------
    causes : List[ValidationError]
        A list of ``ValidationError`` exceptions containing the failure for
        each of the members of the union.

    """

    def __init__(self, *args, causes, **kwargs):
        super().__init__(*args, **kwargs)
        self.causes = causes


class MismatchError(ValidationError):
    """Error raised when some there are either unknown or """

    def __init__(self, missing, unknown):
        self.missing = missing
        self.unknown = unknown
        super().__init__(missing, unknown)

    def __str__(self):
        if self.missing:
            m = f"The following required keys are missing: {self.missing}."
        else:
            m = ""
        if self.unknown:
            u = f"The following keys are unknown: {self.unknown}."
        else:
            u = ""
        return f'{m} {u}'


class WrongKeysError(MismatchError):
    """Error raised when the keys provided by the input do not match those
    required by the specification.

    Parameters
    ----------
    missing : set
        Keys that are required my the specification and missing in the input.

    unknown : set
        Keys that are present in the input but unknown to the specification.

    valid : set
        The set of all valid keys.
    """

    def __init__(self, missing, unknown, valid, header=''):
        self.valid = valid
        self.header = header
        super().__init__(missing, unknown)

    def __str__(self):
        alts = (
            str(AlternativeDisplay(bad_item=u, alternatives=self.valid))
            for u in self.unknown
        )
        if self.header:
            texts = [self.header]
        else:
            texts = []
        texts += [super().__str__(), *alts]
        if self.unknown:
            texts.append(f"All valid options are:\n{print_list(sorted(self.valid))}")
        return '\n'.join(texts)


class WrongTypeError(ValidationError, TypeError):
    """Exception raised when some input is of the wrong type.
    """


class NotAnEnumItemError(AlternativeDisplay, ValidationError, ValueError):
    """Exception raised when a string input is not an Enum name.

    Parameters
    ----------
    bad_item : str
        The value of the wrong item.
    enum_class : :py:class:`type`, :py:class:`enum.Enum` subclass
        The enum class that does not contain ``bad_item``
    """

    def __init__(self, bad_item, enum_class):
        super().__init__(
            f"{bad_item!r} is not a valid member of {enum_class.__name__!r}.",
            bad_item=bad_item,
            alternatives=enum_class.__members__,
        )

    def __str__(self):
        allvals_text = f"All valid values are:\n{print_list(self.alternatives)}"
        return f'{super().__str__()}\n{allvals_text}'


class WrongFieldError(ValidationError):
    """Exception raised when some field (e.g. in a mapping or dataclass) cannot
    be processed correctly.

    Parameters
    ----------
    wrong_field : Any
        The key in the input mapping that caused the error.

    Notes
    -----
    The ``__cause__`` attribute of the exception will contain the underlying
    reason for the error.
    """

    def __init__(self, *args, wrong_field, **kwargs):
        self.wrong_field = wrong_field
        super().__init__(*args, **kwargs)


class WrongListItemError(ValidationError):
    """Exception raised when some item in a list cannot be processed correctly.

    Parameters
    ----------
    wrong_index : int
        The index in the list that caused the error.

    Notes
    -----
    The ``__cause__`` attribute of the exception will contain the underlying
    reason for the error.
    """

    def __init__(self, *args, wrong_index, **kwargs):
        self.wrong_index = wrong_index
        super().__init__(*args, **kwargs)
