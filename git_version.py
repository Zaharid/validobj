import subprocess


def simple_call(s: str) -> str:
    return subprocess.run(
        s.split(), capture_output=True, text=True, check=True
    ).stdout.strip()


def version_from_git():
    tag, rev, hashstr = simple_call('git describe --tags --dirty').split('-', 2)
    return f'{tag}.{rev}+{hashstr}'


__version__ = version_from_git()
print(__version__)
