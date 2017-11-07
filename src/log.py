import sys
from enum import Enum

class logModes(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    FULL = 4

    # Use minus codes for errors/warnings
    ERROR = -1

class log():
    # Default logging mode
    mode = logModes.LOW

    def __init__(self):
        pass

    # Log text directly
    @staticmethod
    def log(logMode: logModes, text: str):
        if log.shouldLog(logMode):
            print(text)

    # Check if we should log (for more advanced print statements)
    @staticmethod
    def shouldLog(logMode: logModes):
        return abs(logMode.value) <= log.mode.value