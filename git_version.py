import subprocess


def simple_call(s: str) -> str:
    return subprocess.run(
        s.split(), capture_output=True, text=True, check=True
    ).stdout.strip()

def version_from_git():
    last_tag_hash = simple_call('git rev-list --tags --max-count=1')
    last_tag = simple_call(f'git describe --tags {last_tag_hash}')
    last_rev = simple_call(f'git rev-list --count {last_tag_hash}..')
    return f'{last_tag}.{last_rev}'

print(version_from_git())
