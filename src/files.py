from src.slack import *

class files():
    def __init__(self, slack: slackData):
        self.slack = slack
        # Map of channel --> Array of files
        self.channel_files = {}

        self.__getFileLocations()

    def __getFileLocations(self):
        log.log(logModes.LOW, "Finding referenced files")

        tot_count = 0

        for channel_name in self.slack.metadata.channels:
            data = self.slack.channel_data[channel_name]
            self.channel_files[channel_name] = []
            count = 0

            for msg in data:
                if self.__addFileIfInMsg(channel_name, msg):
                    count += 1

            log.log(logModes.MEDIUM, str(count) + " files found in #" + channel_name)
            tot_count += count

        log.log(logModes.LOW, "Found " + str(tot_count) + " files")

    def __addFileIfInMsg(self, channel_name, msg):
        if 'subtype' not in msg:
            return False

        if msg['subtype'] == 'file_share' and msg['upload']:
            self.channel_files[channel_name].append(msg)
            return True
        return False