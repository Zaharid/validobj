import sys
import dataclasses
import enum
from typing import Mapping, Set, Tuple, List

import ruamel.yaml as yaml

from yaml_processing import parse_yaml_inp, ValidationError


class DiskPermissions(enum.Flag):
    READ = enum.auto()
    WRITE = enum.auto()
    EXECUTE = enum.auto()


class OS(enum.Enum):
    mac = enum.auto()
    windows = enum.auto()
    linux = enum.auto()


@dataclasses.dataclass
class Job:
    name: str
    os: Set[OS]
    script_path: str
    framework_version: Tuple[int, int] = (1, 0)
    disk_permissions: DiskPermissions = DiskPermissions.READ


@dataclasses.dataclass
class CIConf:
    stages: List[Job]
    global_environment: Mapping[str, str] = dataclasses.field(default_factory=dict)


inp = yaml.round_trip_load(
    """
global_environment: {"CI_ACTIVE": "1"}
stages:
  - name: compile
    os: [linux, mac]
    script_path: "build.sh"
  - name: test
    os: [linux, mac]
    script: "test.sh"
"""
)




try:
    parse_yaml_inp(inp, CIConf)
except ValidationError as e:
    print(e)
    sys.exit(1)
