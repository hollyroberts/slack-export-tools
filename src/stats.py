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
        self.tot_messages = sum(self.users.values())

    def exportPostStats(self):
        wb = Workbook()
        out_file = io.stats_dir + "Post stats.xlsx"

        self.__createColumns(wb)
        self.__addUserStats(wb)

        log.log(logModes.LOW, "Exporting statistics to '" + out_file + "'")
        io.ensureDir(io.stats_dir)
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

    def __addUserStats(self, wb: Workbook):
        wb_users = wb.get_sheet_by_name('Users')

        # Iterate over users instead of map so it's in alphabetical order
        i = 0
        for user in self.slack.metadata.users:
            # Calculate info
            messages = self.users[user]
            percentage = messages / self.tot_messages
            percentage = round(percentage, 3)

            # Save into workbook
            wb_users.cell(row=(i + 2), column=1).value = user
            wb_users.cell(row=(i + 2), column=2).value = messages
            wb_users.cell(row=(i + 2), column=2).number_format = "0"
            wb_users.cell(row=(i + 2), column=3).value = percentage
            wb_users.cell(row=(i + 2), column=3).number_format = "0.0%"

            i += 1

    def __createColumns(self, wb: Workbook):
        # Create two sheets for users and channels
        wb_users = wb.active
        wb_users.title = "Users"
        wb_channels = wb.create_sheet(title="Channels")

        # Add column names
        wb_users['A1'] = "Username"
        wb_users['B1'] = "Messages"
        wb_users['C1'] = "Percentage"

        wb_channels['A1'] = "Channel"
        wb_channels['B1'] = "Messages"
        wb_channels['C1'] = "Percentage"