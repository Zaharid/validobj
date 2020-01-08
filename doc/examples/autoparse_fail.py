from autoparse_decorator import autoparse


@autoparse
def f(a: int, b: str, c, d=1, *args: int, e: str = 'Hi', **kwargs: tuple):
    print(a, b, c, d, e, args, kwargs)


f(1, "b", 3, 1, 100, 20, 40, x=[2], y=[3])
f(1, "b", 3, 1, 100, 20, 40, x=[2], y=3)
