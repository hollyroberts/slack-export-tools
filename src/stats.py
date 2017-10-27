from openpyxl import Workbook

from src.slack import *

class stats():
    def __init__(self, slack: slackData):
        self.slack = slack

        # Initialise blank maps and then calculate stats
        self.users = {}
        for u in self.slack.metadata.users:
            self.users[u] = 0
        self.channels = {}

        self.__calculateStats()

    def exportPostStats(self):
        wb = Workbook()
        out_file = io.stats_dir + "Post stats.xlsx"

        wb_users = wb.active
        wb_users.title = "Users"

        wb_channels = wb.create_sheet(title="Channels")

        if not os.path.exists(io.stats_dir):
            os.makedirs(io.stats_dir)

        log.log(logModes.LOW, "Exporting stats to " + out_file)
        wb.save(filename=out_file)

    def __calculateStats(self):
        log.log(logModes.LOW, "Calculating statistics")

        # Iterate over history, update maps
        for channel in self.slack.metadata.channels:
            channel_count = 0

            for msg in self.slack.channel_data[channel]:
                if ('subtype' not in msg) and (msg['user'] != 'USLACKBOT'):
                    channel_count += 1
                    self.users[self.slack.metadata.getUserName(msg)] += 1

            self.channels[channel] = channel_count