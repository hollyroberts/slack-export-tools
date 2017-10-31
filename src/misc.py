import datetime
import sys
from enum import Enum

class dateModes(Enum):
    ISO8601 = '%Y-%m-%d'
    UK = '%d/%m/%Y'

class misc():
    dateMode = dateModes.ISO8601

    __TRUE_STRINGS = ['T', 'TRUE']
    __FALSE_STRINGS = ['F', 'FALSE']

    def __init__(self):
        pass

    # Types
    @staticmethod
    def padInt(val: int, length=2):
        ret = str(val)

        while len(ret) < length:
            ret = "0" + ret

        return ret

    @staticmethod
    def strToBool(s: str):
        # Type checks
        if type(s) == bool:
            return s
        elif type(s) != str:
            return False

        if s.upper() in misc.__TRUE_STRINGS:
            return True
        elif s.upper() in misc.__FALSE_STRINGS:
            return False
        else:
            print("Could not interpret '" + s + "' as boolean, assuming FALSE")
            return False

    @staticmethod
    def custStrToBool(s: str, pattern: str):
        if type(s) == bool:
            return s

        return s.upper() == pattern.upper()

    @staticmethod
    def strToEnum(enumType, newMode: str):
        for i in enumType:
            if i.name == newMode.upper() and i.value > 0:
                return i

        # Remove modes from enum class name
        enum_str = enumType.__name__[:5]

        sys.exit("Could not interpret " + enum_str + " mode. Please use one of the following: " + ", ".join(i.name for i in enumType if i.value > 0))

    # Dates/times
    @staticmethod
    def formatDate(d: datetime.date):
        return d.strftime(dateModes.UK.value)

    def daterange(d1, d2):
        # https://stackoverflow.com/a/14288620
        return (d1 + datetime.timedelta(days=i) for i in range((d2 - d1).days + 1))