import sys
from enum import Enum

class logModes(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3

    # Use minus codes for errors/warnings
    ERROR = -1

class log():
    # Default logging mode
    __mode = logModes.LOW

    def __init__(self):
        pass

    # Change logging mode using strings, since we will be interpreting directly from the args
    @staticmethod
    def setModeStr(newMode: str):
        for i in logModes:
            if i.name == newMode.upper() and i.value > 0:
                log.__mode = i
                return

        sys.exit("Incorrect log mode specified. Please use one of the following: " + ", ".join(i.name for i in logModes if i.value > 0))

    # Log text directly
    @staticmethod
    def log(logMode: logModes, text: str):
        if log.shouldLog(logMode):
            print(text)

    # Check if we should log (for more advanced print statements)
    @staticmethod
    def shouldLog(logMode: logModes):
        return abs(logMode.value) <= log.__mode.value