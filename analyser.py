# IMPORTS
import json
import os
import sys
import datetime
import re

# CONSTANTS
LOG_MODES = ("LOW", "MEDIUM", "HIGH")
LOG_MODE = "LOW"

SUBTYPES_SIMPLE = ('bot_add',
                   'bot_remove',
                   'channel_archive',
                   'channel_join',
                   'channel_leave',
                   'channel_name',
                   'channel_purpose',
                   'channel_topic',
                   'channel_unarchive')

SUBTYPES_COMPLEX = ('bot_message',
                    'bot_message') # Because python interprets a single element set as not a set :(

SLACK_HTML_ENCODING = {'&amp;': '&',
                       '&lt;': '<',
                       '&gt;': '>'}

# Each switch maps to a 2 element array
# The first element is boolean and determines whether the switch requires additional data
# If not the default data is contained in the second item
SWITCH_CHAR = '-'
SWITCH_DATA = {'i': [True, ''],
               'e': [False, 'export'],
               'ej': [False, 'export_json'],
               'l': [True, ''],
               'o': [True, '']}

# RUNTIME OPTIONS
SWITCHES = {}
SOURCE_DIR = ""
EXPORT_DIR = ""

# VARS
# Slack data
users = []
users_map = {}
channels = []
channel_data = {}

# Export state
last_date = None
last_user = None


# FUNCS
# Loading
def loadJSONFile(file):
    loc = SOURCE_DIR + file

    if (LOG_MODES.index(LOG_MODE) >= LOG_MODES.index("HIGH")):
        print("Reading '" + loc + "'")

    file = open(loc, "r", encoding="utf8")
    data = file.read()
    data = json.loads(data)
    file.close()

    return data

def loadSlack():
    global users, users_map
    global channels, channel_data

    print("Loading slack from: " + SOURCE_DIR)

    # Load channels and users
    channels = loadChannels()
    users_map = loadUserMapping()
    users = sorted(list(users_map.values()))

    if (LOG_MODES.index(LOG_MODE) >= LOG_MODES.index("MEDIUM")):
        print("Users and channels loaded")
        print("Loading channel data")

    # Load channel data
    for channel in channels:
        if (LOG_MODES.index(LOG_MODE) >= LOG_MODES.index("MEDIUM")):
            print("Loading channel data for #" + channel)

        channel_data[channel] = loadChannelData(channel)

    print("Slack loaded")

def loadChannels():
    channel_data = loadJSONFile("channels.json")

    # Build the array of channel names
    channels = []
    for i in channel_data:
        channels.append(i['name'])
    channels.sort()

    return channels

def loadChannelData(channel: str):
    data = []

    # Use os.listdir to find all files in the subdirectory
    # This should be in chronological order, due to the naming scheme used by slack
    for file in os.listdir(SOURCE_DIR + channel):
        if file.endswith(".json"):
            file_data = loadJSONFile(channel + "\\" + file)
            data += file_data

    return data

def loadUserMapping():
    user_data = loadJSONFile("users.json")

    # Build the map from id --> name
    users = {}
    for i in user_data:
        users[i['id']] = i['name']

    return users

# Statistics
def calculateScores(users, channels):
    # Build arrays for users and channels
    user_scores = {}
    for user in users:
        user_scores[users[user]] = 0

    channel_scores = {}
    for i in channels:
        channel_scores[i] = 0

    # Iterate over channels
    for channel in channels:
        for file in os.listdir(SOURCE_DIR + channel):
            if file.endswith(".json"):
                # Process the file, get the scores for each user
                file_user_scores = calculateFileScores(channel + "\\" + file, users)

                # Update user_scores and channel_scores
                for username in file_user_scores:
                    user_scores[username] += file_user_scores[username]
                    channel_scores[channel] += file_user_scores[username]

    return user_scores, channel_scores

def calculateFileScores(file_loc, users):
    data = loadJSONFile(file_loc)
    user_scores = {}

    print(file_loc)

    # Iterate over messages, only include human messages (ones without subtypes)
    for i in data:
        if ('subtype' not in i) and (i['user'] != 'USLACKBOT'):
            # Translate UUID to user name
            username = i['user']
            username = users[username]

            # Add to scores
            if username in user_scores:
                user_scores[username] += 1
            else:
                user_scores[username] = 0

    return user_scores

def printFinalStats(user_scores, channel_scores):
    tot_messages = 0
    for i in channel_scores:
        tot_messages += channel_scores[i]

    print("Messages posted: " + str(tot_messages))
    print("\nChannel Stats:")

    for i in sorted(channel_scores.keys()):
        messages = channel_scores[i]
        percentage = (messages * 100) / tot_messages
        percentage = round(percentage, 1)

        print("#" + i + "," + str(messages) + "," + str(percentage) + "%")
        # print("#" + i + ":\t" + str(messages) + " (" + str(percentage) + "%)")

    print("\nUser Stats:")
    for i in sorted(user_scores.keys()):
        messages = user_scores[i]
        percentage = (messages * 100) / tot_messages
        percentage = round(percentage, 1)

        print(i + "," + str(messages) + "," + str(percentage) + "%")
        # print(i + ":\t" + str(messages) + " (" + str(percentage) + "%)")

# Exporting
def exportChosenOptions():
    if 'e' in SWITCHES:
        exportChannelData(EXPORT_DIR + SWITCHES['e'])

    if 'ej' in SWITCHES:
        exportChannelData(EXPORT_DIR + SWITCHES['ej'], as_json=True)

def exportChannelData(folder_loc: str, as_json=False):
    print("Exporting channel data to '" + folder_loc + "'")

    if not os.path.exists(folder_loc):
        os.makedirs(folder_loc)

    for channel in channels:
        data = channel_data[channel]

        loc = folder_loc + "\\#" + channel
        if (as_json):
            loc += ".json"
        else:
            loc += ".txt"

        if (LOG_MODES.index(LOG_MODE) >= LOG_MODES.index("MEDIUM")):
            print("Exporting #" + channel + " to '" + loc + "'")

        if (as_json):
            data = json.dumps(data, indent=4)
        else:
            data = formatChannelJSON(data)

        file = open(loc, "w", encoding="utf8")
        file.write(data)
        file.close()

    print("Data exported")

def formatChannelJSON(raw_json):
    # Reset global vars
    global last_date, last_user

    last_date = None
    last_user = None

    # Build and return data
    formatted_data = ""
    for msg in raw_json:
        formatted_data += formatMessageJSON(msg)
    formatted_data.strip()

    return formatted_data

def formatMessageJSON(msg):
    global last_date

    ret = ""

    # Get timestamp and process
    timestamp = msg['ts']
    dt = datetime.datetime.fromtimestamp(float(timestamp))
    date = dt.date()
    time = dt.time()

    if last_date == None or last_date < date:
        ret += " -- " + str(date.day) + "/" + str(date.month) + "/" + str(date.year) + " -- \n"
        last_date = date

    ret += "[" + padInt(time.hour) + ":" + padInt(time.minute) + "]\t"

    # Get subtype
    subtype = None
    if 'subtype' in msg:
        subtype = msg['subtype']

    # Do stuff based on the subtype
    if subtype in SUBTYPES_SIMPLE:
        ret += improveMsgContents(msg['text'], include_ampersand=False) + "\n"
    elif subtype in SUBTYPES_COMPLEX:
        ret += getUserName(msg) + ": " + getMsgContents(msg) + "\n"
    else:
        ret += getUserName(msg) + ": " + getMsgContents(msg) + "\n"

    return ret

def getMsgContents(msg):
    # If text is available (it sometimes might not be) then add it first
    # If attachments exist then add them
    ret = ""

    if 'text' in msg:
        ret += improveMsgContents(msg['text'])

    return ret

def padInt(val: int, length=2):
    ret = str(val)

    while len(ret) < length:
        ret = "0" + ret

    return ret

def improveMsgContents(msg: str, include_ampersand=True):
    # Replace HTML encoded characters
    for i in SLACK_HTML_ENCODING:
        msg = msg.replace(i, SLACK_HTML_ENCODING[i])

    # Make mentions readable
    mentions = re.finditer('<@U([^|>]+)>', msg)

    for match in mentions:
        new_text = ""
        if include_ampersand:
            new_text += "@"

        ID = match.group()[2:-1]

        if ID == 'SLACKBOT':
            new_text += "Slackbot"
        elif ID in users_map:
            new_text += users_map[ID]
        else:
            new_text += ID

        msg = msg.replace(match.group(), new_text)

    # Improve indentation (use spaces instead of tabs, I expect most people to view the data using a monospaced font)
    # At least this works for notepad and notepad++
    msg = msg.replace("\n", "\n        ")

    return msg

def getUserName(message):
    if 'user' in message:
        username = message['user']

        if username == "USLACKBOT":
            return 'Slackbot'
        else:
            return users_map[username]

    if 'username' in message:
        username = message['username']
        if username in users_map:
            return users_map[username]
        else:
            return username

    return "Unknown"

# Output info
def outputUsers():
    print("List of users:")
    for i in users:
        print(i)

def outputSubtypes():
    subtypes = set()

    print("Scanning history")
    for channel in channel_data:
        for message in channel_data[channel]:
            if "subtype" in message:
                subtypes.add(message['subtype'])

    print("Subtypes found in message history:")
    for i in sorted(subtypes):
        print(i)

# Misc.
def loadArgs():
    interpretArgs(sys.argv)
    setSlackSource()
    setLogMode()

def interpretArgs(argv):
    # Remove script location
    argv = argv[1:]

    i = 0
    while i < len(argv):
        # Argument must be a switch
        if not argv[i].startswith(SWITCH_CHAR):
            sys.exit("Incorrect args. Expected a switch")

        # Switch must be valid
        switch = argv[i][1:]
        if not switch in SWITCH_DATA:
            sys.exit("Incorrect args. Switch '" + switch + "' not found")

        # Switch must not have been added already
        if switch in SWITCHES:
            sys.exit("Incorrect args. Switch '" + switch + "' has already been added")

        # Does switch require an argument
        if SWITCH_DATA[switch][0]:
            i += 1
            if i >= len(argv):
                sys.exit("Incorrect args. Required an argument for '" + switch + "', but ran out of arguments")

            if argv[i].startswith(SWITCH_CHAR):
                sys.exit("Incorrect args. Required argument for '" + switch + "', but found a switch")

            SWITCHES[switch] = argv[i]
        else:
            i += 1

            # Default if there are no more arguments
            if i >= len(argv):
                SWITCHES[switch] = SWITCH_DATA[switch][1]
                break

            # If next argument is a switch use default data
            if argv[i].startswith(SWITCH_CHAR):
                SWITCHES[switch] = SWITCH_DATA[switch][1]
                continue

            SWITCHES[switch] = argv[i]

        i += 1

def setSlackSource():
    global SOURCE_DIR

    if not 'i' in SWITCHES:
        return

    if SWITCHES['i'] == "":
        return

    SOURCE_DIR = SWITCHES['i']
    if not SOURCE_DIR.endswith("\\"):
        SOURCE_DIR += "\\"

def setLogMode():
    global LOG_MODE

    if not 'l' in SWITCHES:
        return

    if SWITCHES['l'].upper() not in LOG_MODES:
        modes = ""
        for i in LOG_MODES:
            modes += i + ", "

        sys.exit("Incorrect log mode specified. Please use one of the following: " + modes[:-2])

    LOG_MODE = SWITCHES['l'].upper()

def setExportLocation():
    global EXPORT_DIR

    if not 'o' in SWITCHES:
        return

    if SWITCHES['o'] == "":
        return

    EXPORT_DIR = SWITCHES['o']
    if not EXPORT_DIR.endswith("\\"):
        EXPORT_DIR += "\\"

# START OF PROGRAM
loadArgs()
loadSlack()
exportChosenOptions()