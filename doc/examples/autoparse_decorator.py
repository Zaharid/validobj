#autoparse_decorator.py

import functools
from typing import get_type_hints
import inspect

from validobj import parse_input, ValidationError


def autoparse(f):
    """Apply ``parse_input`` to each argument of the decorated function, based
    on its type annotation."""
    sig = inspect.signature(f)
    # Use this instead of signature to resolve delayed annotations.
    hints = get_type_hints(f)

    @functools.wraps(f)
    def f_(*args, **kwargs):
        ba = sig.bind(*args, **kwargs)
        newargs = ba.arguments.copy()
        for argname, argvalue in ba.arguments.items():
            param = sig.parameters[argname]
            if argname not in hints:
                continue
            spec = hints[argname]
            try:
                # Handle variable keyword arguments. The type annotation applies to each value.
                if param.kind is param.VAR_KEYWORD:
                    newargs[argname] = {
                        k: parse_input(v, spec) for k, v in argvalue.items()
                    }

                # Handle variable positional arguments. The type annotation applies to each value.
                elif param.kind is param.VAR_POSITIONAL:
                    newargs[argname] = tuple(parse_input(v, spec) for v in argvalue)
                else:
                    newargs[argname] = parse_input(argvalue, spec)
            except ValidationError as e:
                # Add information on which argument failed
                raise ValidationError(f"Failed processing argument {argname!r}") from e

        ba.arguments = newargs

        return f(*ba.args, **ba.kwargs)

    return f_
