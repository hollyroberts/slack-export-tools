class misc():
    __TRUE_STRINGS = ['T', 'TRUE']
    __FALSE_STRINGS = ['F', 'FALSE']

    def __init__(self):
        pass

    @staticmethod
    def padInt(val: int, length=2):
        ret = str(val)

        while len(ret) < length:
            ret = "0" + ret

        return ret

    @staticmethod
    def strToBool(s: str):
        if s.upper() in misc.__TRUE_STRINGS:
            return True
        elif s.upper() in misc.__FALSE_STRINGS:
            return False
        else:
            print("Could not interpret '" + s + "' as boolean, assuming FALSE")
            return False