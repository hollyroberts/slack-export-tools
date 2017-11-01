import datetime
import sys
from enum import Enum

class dateModes(Enum):
    ISO8601 = '%Y-%m-%d'
    UK = '%d/%m/%Y'

    def toExcel(self):
        # Only support values we use
        s = self.value
        s = s.replace("%d", "DD")
        s = s.replace("%m", "MM")
        s = s.replace("%Y", "YYYY")
        return s

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
            if i.name == newMode.upper():
                # Don't allow negative enums
                if type(i.value) is not int:
                    return i
                if i.value > 0:
                    return i

        # Remove modes from enum class name
        enum_str = enumType.__name__[:-5]

        # List of valid enums should exclude enums with negative values
        valid_enums = []
        for i in enumType:
            if type(i.value) is int:
                if i.value > 0:
                    valid_enums.append(i.name)
            else:
                valid_enums.append(i.name)

        sys.exit("Could not interpret " + enum_str + " mode. Please use one of the following: " + ", ".join(valid_enums))

    # Dates/times
    @staticmethod
    def interpretDate(date_str: str):
        try:
            return datetime.datetime.strptime(date_str, str(misc.dateMode.value))
        except ValueError as e:
            sys.exit("Could not convert '" + date_str + "' using " + misc.dateMode.name + " encoding (" + misc.dateMode.toExcel() + ")")

    @staticmethod
    def formatDate(d: datetime.date):
        return d.strftime(str(misc.dateMode.value))

    @staticmethod
    def daterange(d1, d2):
        # https://stackoverflow.com/a/14288620
        return (d1 + datetime.timedelta(days=i) for i in range((d2 - d1).days + 1))