from enum import IntEnum
from typing import Any, List

from attacks.attack import AttackOptions
from attacks.util import print_error, print_warning


class Speed(IntEnum):
    FAST = 5 # nmap timing template insane
    MEDIUM = 3 # nmap timing template normal
    SLOW = 1 # nmap timing template sneaky


class NmapAttackOptions(AttackOptions):
    speed: str

    def __init__(self, **kwargs: Any):
        self._set_options_to_none()
        self._set_defaults()
        super().__init__(**kwargs)

    def _set_options_to_none(self) -> None:
        default_options = dict.fromkeys(self._options(), None)
        default_options = _set_custom_defaults(default_options)
        self.__dict__.update(default_options)

    @classmethod
    def _options(cls) -> List[str]:
        _set_custom_description(cls)
        return [att for att in dir(cls) if not att.startswith("_")]

    def _set_defaults(self) -> None:
        pass


def _set_custom_defaults(default_options):
    default_options["speed"] = "fast"
    default_options["speed_choices"] = ["slow", "medium", "fast"]

    return default_options


def _set_custom_description(cls):
    cls.speed = "Attack speed [slow, medium, (fast)]"


def get_speed(options) -> int:
    speed = options.speed.upper()
    try:
        return Speed[speed]
    except KeyError:
        print_error(f"Invalid option: {options.speed}")
        options.speed = "fast"
        print_warning(f"Default to: {options.speed}")
        return Speed[options.speed.upper()]
