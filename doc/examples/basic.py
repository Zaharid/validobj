import dataclasses
import enum
from typing import Literal

from validobj import parse_input

inp = {
    'global_environment': {'CI_ACTIVE': '1'},
    'stages': [
        {
            'name': 'compile',
            'os': ['linux', 'mac'],
            'script_path': 'build.sh',
            'disk_permissions': ['READ', 'WRITE', 'EXECUTE'],
        },
        {
            'name': 'test',
            'os': ['linux', 'mac'],
            'script_path': 'test.sh',
            'framework_version': [4, 0],
        },
    ],
}


class DiskPermissions(enum.Flag):
    READ = enum.auto()
    WRITE = enum.auto()
    EXECUTE = enum.auto()



@dataclasses.dataclass
class Job:
    name: str
    os: set[Literal['windows', 'mac', 'linux']]
    script_path: str
    framework_version: tuple[int, int] = (1, 0)
    disk_permissions: DiskPermissions = DiskPermissions.READ


@dataclasses.dataclass
class CIConf:
    stages: list[Job]
    global_environment: dict[str, str] = dataclasses.field(default_factory=dict)



print(parse_input(inp, CIConf))
# This results in a dataclass instance with the correct types:
#
#CIConf(
#    stages=[
#        Job(
#            name='compile',
#            os={'linux', 'mac'},
#            script_path='build.sh',
#            framework_version=(1, 0),
#            disk_permissions=<DiskPermissions.EXECUTE|WRITE|READ: 7>,
#        ),
#        Job(
#            name='test',
#            os={'linux', 'mac'},
#            script_path='test.sh',
#            framework_version=(4, 0),
#            disk_permissions='<DiskPermissions.READ: 1>',
#        ),
#    ],
#    global_environment={'CI_ACTIVE': '1'},
#)
#
