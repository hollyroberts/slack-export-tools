from src.slack import *

class pins():
    def __init__(self, slack: slackData):
        self.slack = slack

    def export(self, dir: str):
        print(dir)