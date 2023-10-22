import sys

# https://docs.pytest.org/en/6.2.x/example/pythoncollection.html#customizing-test-collection


if sys.version_info < (3, 12):  # pragma: nocover
    collect_ignore = ["test_type_syntax.py"]
