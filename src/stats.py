from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, Side

from src.slack import *

class stats():
    def __init__(self, slack: slackData):
        self.slack = slack

        # Initialise blank maps and then calculate stats
        self.user_count = {}
        for u in self.slack.metadata.users:
            self.user_count[u] = 0
        self.channel_count = {}

        self.__calculateStats()
        self.tot_messages = sum(self.user_count.values())

    def exportPostStats(self):
        wb = Workbook()
        out_file = io.stats_dir + "Post stats.xlsx"

        # Create two sheets for users and channels
        wb_users = wb.active
        wb_users.title = "Users"
        wb_channels = wb.create_sheet(title="Channels")
        self.__createColumns(wb_channels)
        self.__createColumns(wb_users)

        # Add data
        wb_channels = wb.get_sheet_by_name("Channels")
        wb_users = wb.get_sheet_by_name("Users")
        self.__addStats(wb_channels, self.slack.metadata.channels, self.channel_count, prefix='#')
        self.__addStats(wb_users, self.slack.metadata.users, self.user_count)

        # Make it pretty
        self.__adjustColumnWidth(wb_channels)
        self.__adjustColumnWidth(wb_users)

        # Save
        log.log(logModes.LOW, "Exporting statistics to '" + out_file + "'")
        io.ensureDir(io.stats_dir)

        try:
            wb.save(filename=out_file)
        except PermissionError:
            log.log(logModes.ERROR, "Could not write to file: Permission Denied")

    def __calculateStats(self):
        log.log(logModes.LOW, "Calculating statistics")

        # Iterate over history, update maps
        for channel in self.slack.metadata.channels:
            channel_count = 0

            for msg in self.slack.channel_data[channel]:
                if ('subtype' not in msg) and (msg['user'] != 'USLACKBOT'):
                    channel_count += 1
                    self.user_count[self.slack.metadata.getUserName(msg)] += 1

            self.channel_count[channel] = channel_count

    def __addStats(self, ws, values_ls: list, values_map: dict, prefix:str=''):
        i = 0
        for val in values_ls:
            # Calculate info
            messages = values_map[val]
            percentage = messages / self.tot_messages
            percentage = round(percentage, 3)

            # Save into workbook
            ws.cell(row=(i + 2), column=1).value = prefix + val
            ws.cell(row=(i + 2), column=2).value = messages
            ws.cell(row=(i + 2), column=2).number_format = "0"
            ws.cell(row=(i + 2), column=3).value = percentage
            ws.cell(row=(i + 2), column=3).number_format = "0.0%"

            # Center 2nd and 3rd column
            ws.cell(row=(i + 2), column=2).alignment = Alignment(horizontal='center')
            ws.cell(row=(i + 2), column=3).alignment = Alignment(horizontal='center')

            i += 1

    def __createColumns(self, ws):
        # Add column names
        ws['A1'] = ws.title[:-1]
        ws['B1'] = "Messages"
        ws['C1'] = "Percentage"

        # Align horizontally messages and percentage aligned
        ws['B1'].alignment = Alignment(horizontal='center')
        ws['C1'].alignment = Alignment(horizontal='center')

        # Make column titles bold and underlined
        ws['A1'].font = Font(bold=True)
        ws['B1'].font = Font(bold=True)
        ws['C1'].font = Font(bold=True)
        ws['A1'].border = Border(bottom=Side(border_style='thin'))
        ws['B1'].border = Border(bottom=Side(border_style='thin'))
        ws['C1'].border = Border(bottom=Side(border_style='thin'))

        # Add filter rules
        ws.auto_filter.ref = "A1:C" + str(len(self.slack.metadata.users))

    def __adjustColumnWidth(self, ws):
        # https://stackoverflow.com/a/39530676

        for col in ws.columns:
            max_length = 0
            column = col[0].column  # Get the column name
            for cell in col:
                try:  # Necessary to avoid error on empty cells
                    if len(str(cell.value)) > max_length:
                        max_length = len(cell.value)
                except:
                    pass
            adjusted_width = (max_length + 0.5) * 1.2
            ws.column_dimensions[column].width = adjusted_width