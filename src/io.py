from src.log import *
import json
import os


class io():
    # Store parts so we can reconstruct the full path
    __html_dir = ""
    __json_dir = ""
    __stats_dir = ""
    __text_dir = ""

    source_dir = ""
    export_dir = ""

    html_dir = __html_dir
    json_dir = __json_dir
    stats_dir = __stats_dir
    text_dir = __text_dir

    def __init__(self):
        pass

    @staticmethod
    def setExportDir(dir: str):
        io.export_dir = io.combinePaths(dir)
        io.html_dir = io.combinePaths(dir, io.__html_dir)
        io.json_dir = io.combinePaths(dir, io.__json_dir)
        io.stats_dir = io.combinePaths(dir, io.__stats_dir)
        io.text_dir = io.combinePaths(dir, io.__text_dir)

    @staticmethod
    def combinePaths(*args: str):
        dir = ""
        for arg in args:
            dir += arg
            if arg != "" and not arg.endswith("\\"):
                dir += "\\"

        return dir

    @staticmethod
    def setHtmlDir(dir: str):
        io.__html_dir = dir
        io.html_dir = io.combinePaths(io.export_dir, io.__html_dir)

    @staticmethod
    def setJsonDir(dir: str):
        io.__json_dir = dir
        io.json_dir = io.combinePaths(io.export_dir, io.__json_dir)

    @staticmethod
    def setStatsDir(dir: str):
        io.__stats_dir = dir
        io.stats_dir = io.combinePaths(io.export_dir, io.__stats_dir)

    @staticmethod
    def setTextDir(dir: str):
        io.__text_dir = dir
        io.text_dir = io.combinePaths(io.export_dir, io.__text_dir)

    @staticmethod
    def ensureDir(dir: str):
        if not os.path.exists(dir):
            os.makedirs(dir)

    @staticmethod
    def loadJSONFile(file):
        loc = io.source_dir + file

        log.log(logModes.HIGH, "Reading '" + loc + "'")

        file = open(loc, "r", encoding="utf8")
        data = file.read()
        data = json.loads(data)
        file.close()

        return data