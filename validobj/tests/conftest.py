import sys

# https://docs.pytest.org/en/6.2.x/example/pythoncollection.html#customizing-test-collection

collect_ignore = []

if sys.version_info < (3, 12):  # pragma: nocover
    collect_ignore += ["test_type_syntax.py"]

if sys.version_info < (3, 14):  # pragma: nocover
    collect_ignore += ["test_delayed_dataclasses.py"]
