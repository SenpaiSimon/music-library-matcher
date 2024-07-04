from enum import Enum

class Status(Enum):
    ERROR = 1
    OK = 2
    SKIPPED = 3
    MISSING = 4
    LONGNAME = 5
    DUPLICATE = 6
    HTTP = 7