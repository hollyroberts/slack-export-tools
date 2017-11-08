from src.export import *
import urllib.request

class files():
    def __init__(self, slack: slackData):
        self.slack = slack
        # Map of channel --> Array of files
        self.channel_files = {}

        self.__getFileLocations()

    def downloadFiles(self):
        log.log(logModes.LOW, "Downloading referenced files found")

        for channel_name in self.slack.metadata.channels:
            log.log(logModes.MEDIUM, "Downloading " + str(len(self.channel_files[channel_name])) + " files from #" + channel_name)
            dir = io.file_dir + channel_name + "\\"
            io.ensureDir(io.file_dir + channel_name)

            for file_msg in self.channel_files[channel_name]:
                self.__downloadFile(file_msg, dir)

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

    def __downloadFile(self, file_msg, file_dir):
        download_url = file_msg['file']['url_private_download']

        file_size = io.bytesToStr(file_msg['file']['size'])

        file_name = file_msg['file']['name']
        file_name = re.sub('[\\\/:*?"<>|]', '', file_name)

        save_name = export.formatTimestamp(file_msg['file']['timestamp'], full=True, min_divide_char=';')
        save_name += "- " + self.slack.metadata.getUserName(file_msg['file']) + " - "
        save_name += file_name

        log.log(logModes.HIGH, "Downloading file from '" + download_url + "' (" + file_size + ")")

        urllib.request.urlretrieve(download_url, file_dir + save_name)