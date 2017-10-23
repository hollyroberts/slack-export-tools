from src.log import *
import json

class io():
    __html_dir = "export_html\\"
    __json_dir = "export_json\\"
    __text_dir = "export_text\\"

    source_dir = ""
    export_dir = ""
    export_html_dir = __html_dir
    export_json_dir = __json_dir
    export_text_dir = __text_dir

    def __init__(self):
        pass

    @staticmethod
    def setExportDir(self, dir: str):
        io.export_dir = dir
        if io.export_dir != "" and not io.export_dir.endswith("\\"):
            io.export_dir += "\\"

        # Update other references
        io.setHtmlDir(io.__html_dir)
        io.setJsonDir(io.__json_dir)
        io.setTextDir(io.__text_dir)

    @staticmethod
    def setHtmlDir(self, dir: str):
        io.export_html_dir = io.export_dir + dir
        if io.export_html_dir != "" and not io.export_html_dir.endswith("\\"):
            io.export_html_dir += "\\"

    @staticmethod
    def setJsonDir(self, dir: str):
        io.export_json_dir = io.export_dir + dir
        if io.export_json_dir != "" and not io.json_html_dir.endswith("\\"):
            io.export_json_dir += "\\"

    @staticmethod
    def setTextDir(self, dir: str):
        io.export_text_dir = io.export_dir + dir
        if io.export_text_dir != "" and not io.export_text_dir.endswith("\\"):
            io.export_text_dir += "\\"

    @staticmethod
    def loadJSONFile(file):
        loc = io.source_dir + file

        log.log(logModes.HIGH, "Reading '" + loc + "'")

        file = open(loc, "r", encoding="utf8")
        data = file.read()
        data = json.loads(data)
        file.close()

        return data