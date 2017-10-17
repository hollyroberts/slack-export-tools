from src.log import *
import json

class io():
    source_dir = ""
    export_dir = ""

    def __init__(self):
        pass

    @staticmethod
    def loadJSONFile(file):
        loc = io.source_dir + file

        log.log(logModes.HIGH, "Reading '" + loc + "'")

        file = open(loc, "r", encoding="utf8")
        data = file.read()
        data = json.loads(data)
        file.close()

        return data