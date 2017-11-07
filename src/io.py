from src.log import *
import json
import os


class io():
    # Store parts so we can reconstruct the full path
    __info_dir = ""
    __pins_dir = ""

    __file_dir = ""
    __html_dir = ""
    __json_dir = ""
    __text_dir = ""

    source_dir = ""
    export_dir = ""

    info_dir = __info_dir
    pins_dir = __pins_dir

    file_dir = __file_dir
    html_dir = __html_dir
    json_dir = __json_dir
    text_dir = __text_dir

    def __init__(self):
        pass

    @staticmethod
    def setExportDir(dir: str):
        io.export_dir = io.combinePaths(dir)

        io.file_dir = io.combinePaths(dir, io.__file_dir)
        io.html_dir = io.combinePaths(dir, io.__html_dir)
        io.info_dir = io.combinePaths(dir, io.__info_dir)
        io.json_dir = io.combinePaths(dir, io.__json_dir)
        io.pins_dir = io.combinePaths(io.export_dir, io.__info_dir, io.__pins_dir)
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
    def setFileDir(dir: str):
        io.__file_dir = dir
        io.file_dir = io.combinePaths(io.export_dir, io.__file_dir)

    @staticmethod
    def setHtmlDir(dir: str):
        io.__html_dir = dir
        io.html_dir = io.combinePaths(io.export_dir, io.__html_dir)

    @staticmethod
    def setJsonDir(dir: str):
        io.__json_dir = dir
        io.json_dir = io.combinePaths(io.export_dir, io.__json_dir)

    @staticmethod
    def setPinsDir(dir: str):
        io.__pins_dir = dir
        io.pins_dir = io.combinePaths(io.export_dir, io.__info_dir, io.__pins_dir)

    @staticmethod
    def setInfoDir(dir: str):
        io.__info_dir = dir
        io.info_dir = io.combinePaths(io.export_dir, io.__info_dir)

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

        log.log(logModes.FULL, "Reading '" + loc + "'")

        file = open(loc, "r", encoding="utf8")
        data = file.read()
        data = json.loads(data)
        file.close()

        return data