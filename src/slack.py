import os

from src.io import *

class slackData():
    def __init__(self):
        # User data
        self.users = []
        self.users_map = {}

        # Channel data
        self.channels = []
        self.channel_map = {}
        self.channel_data = {}

        # Threaded messages
        self.channel_threads = {}

        self.__loadSlack()

    def getUserName(self, msg):
        if 'user' in msg:
            username = msg['user']

            if username == "USLACKBOT":
                return 'Slackbot'
            else:
                return self.users_map[username]

        if 'username' in msg:
            username = msg['username']
            if username in self.users_map:
                return self.users_map[username]
            else:
                return username

        return "Unknown"

    def __loadSlack(self):
        print("Loading slack from: " + io.source_dir)

        # Load channels and users
        self.channel_map = self.__loadChannelMap()
        self.channels = sorted(self.channel_map.values())
        self.users_map = self.__loadUserMapping()
        self.users = sorted(list(self.users_map.values()))

        if log.shouldLog(logModes.MEDIUM):
            print("Users and channels loaded")
            print("Loading channel data")

        # Load channel data and threaded messages
        for channel in self.channels:
            log.log(logModes.MEDIUM, "Loading channel data for #" + channel)
            data = self.__loadChannelData(channel)

            self.channel_data[channel] = data
            self.channel_threads[channel] = self.__loadChannelThreads(data)

        print("Slack loaded")

    def __loadChannelMap(self):
        channel_data = io.loadJSONFile("channels.json")

        # Build the array of channel names
        map = {}
        for i in channel_data:
            map[i['id']] = i['name']

        return map

    def __loadChannelData(self, channel: str):
        data = []

        # Use os.listdir to find all files in the subdirectory
        # This should be in chronological order, due to the naming scheme used by slack
        for file in os.listdir(io.source_dir + channel):
            if file.endswith(".json"):
                file_data = io.loadJSONFile(channel + "\\" + file)
                data += file_data

        return data

    def __loadChannelThreads(self, data):
        msgs = {}

        for msg in data:
            if not 'thread_ts' in msg:
                continue

            # Do not save the parent
            if msg['thread_ts'] != msg['ts']:
                msgs[msg['ts']] = msg

        return msgs

    def __loadUserMapping(self):
        user_data = io.loadJSONFile("users.json")

        # Build the map from id --> name
        users = {}
        for i in user_data:
            users[i['id']] = i['name']

        return users