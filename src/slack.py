import copy

from src.io import *
from src.misc import *

class slackData():
    def __init__(self):
        self.metadata = slackMetaData()
        self.channel_data = {}
        self.channel_threads = {}

    def clone(self):
        clone = slackData()

        clone.metadata = self.metadata.clone()
        clone.channel_data = copy.deepcopy(self.channel_data)
        clone.channel_threads = copy.deepcopy(self.channel_threads)

        return clone

    def filter(self, date_start, date_end):
        # Log dates
        if date_start is None and date_end is None:
            return
        if date_end is None:
            log.log(logModes.LOW, "Filtering messages to dates after " + misc.formatDate(date_start) + " (inclusive)")
        elif date_start is None:
            log.log(logModes.LOW, "Filtering messages to dates before " + misc.formatDate(date_end) + " (exclusive)")
        else:
            log.log(logModes.LOW, "Filtering messages to dates between " + misc.formatDate(date_start) + " (inclusive) and " + misc.formatDate(date_end) + " (exclusive)")

        for c in self.metadata.channels:
            self.channel_data[c] = list(msg for msg in self.channel_data[c] if self.includeMsgTS(msg, date_start, date_end))
            self.channel_threads[c] = self.__loadChannelThreads(self.channel_data[c])

    def includeMsgTS(self, msg, ds, de):
        timestamp = msg['ts']
        dt = datetime.datetime.fromtimestamp(float(timestamp))

        if ds is not None and dt < ds:
            return False
        if de is not None and dt > de:
            return False
        return True

    def loadSlack(self, source_dir: str):
        print("Loading slack from '" + source_dir + "'")

        # Load metadata
        self.metadata.loadSlack()

        if log.shouldLog(logModes.MEDIUM):
            print("Users and channels loaded")
            print("Loading channel data")

        # Load channel data and threaded messages
        for channel in self.metadata.channels:
            log.log(logModes.MEDIUM, "Loading channel data for #" + channel)
            data = self.__loadChannelData(channel)

            self.channel_data[channel] = data
            self.channel_threads[channel] = self.__loadChannelThreads(data)

        print("Slack loaded")

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

class slackMetaData():
    def __init__(self):
        # User metadata
        self.users = []
        self.users_json = []
        self.users_map = {}

        # Channel metadata
        self.channels = []
        self.channels_json = []
        self.channel_map = {}

        self.team_id = ""

    def getUserName(self, msg):
        # Prefer user over username field, since this is an ID and username can be present but blank
        if 'user' in msg:
            username = msg['user']

            if username == "USLACKBOT":
                return 'Slackbot'
            else:
                return self.users_map[username]

        if 'username' in msg:
            return msg['username']

        return "Unknown"

    def isDefinitelyUser(self, json):
        # Only return true if the 'user' field directly maps to a known user that is not a bot
        if 'user' not in json:
            return False

        username = json['user']
        if username == "USLACKBOT":
            return False

        if username not in self.users_map:
            return False

        return not self.users_json[username]['is_bot']

    def loadSlack(self):
        # Load channels and users
        self.channels_json = io.loadJSONFile("channels.json")
        self.channel_map = self.__mapJson(self.channels_json)
        self.channels = sorted(self.channel_map.values())
        self.channels_json = self.__arrayToMap(self.channels_json)

        self.users_json = io.loadJSONFile("users.json")
        self.users_map = self.__mapJson(self.users_json)
        self.users = sorted(list(self.users_map.values()))
        self.users_json = self.__arrayToMap(self.users_json)

        # The Team ID is in each users profile, so we can get it this way
        # Not very clean though :/
        self.team_id = next(iter(self.users_json.values()))['profile']['team']

    def clone(self):
        clone = slackMetaData()

        clone.users = copy.deepcopy(self.users)
        clone.users_map = copy.deepcopy(self.users_map)
        clone.channels = copy.deepcopy(self.channels)
        clone.channel_map = copy.deepcopy(self.channel_map)

        return clone

    def __arrayToMap(self, json):
        map = {}
        for entry in json:
            map[entry['id']] = entry
        return map

    def __mapJson(self, data):
        map = {}
        for i in data:
            map[i['id']] = i['name']

        return map