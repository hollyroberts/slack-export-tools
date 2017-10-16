# IMPORTS
import json
import os
import datetime
import re

from src.log import *

# CONSTANTS
SUBTYPES_NO_PREFIX = ('channel_archive',
                      'channel_join',
                      'channel_leave',
                      'channel_name',
                      'channel_purpose',
                      'channel_topic',
                      'channel_unarchive',
                      'pinned_item')

SUBTYPES_REDUCED_PREFIX = ('bot_add',
                           'bot_remove',
                           'reminder_add')

SUBTYPES_CUSTOM = ('me_message',
                   'reply_broadcast')

SUBTYPES_IGNORE = ('thread_broadcast',)

SLACK_HTML_ENCODING = {'&amp;': '&',
                       '&lt;': '<',
                       '&gt;': '>'}

ATTACHMENT_FIELDS = ('fields',
                     'subtext',
                     'text',
                     'title',
                     'title_link')

INDENTATION = "        "  # 8 spaces
INDENTATION_SHORT = "     "  # 5 spaces

TRUE_STRINGS = ['T', 'TRUE']
FALSE_STRINGS = ['F', 'FALSE']

# Each switch maps to a 2 element array
# The first element is boolean and determines whether the switch requires additional data
# If not the default data is contained in the second item
SWITCH_CHAR = '-'
SWITCH_DATA = {'c': [True, ''],
               'i': [True, ''],
               'e': [False, 'export'],
               'ej': [False, 'export_json'],
               'l': [True, ''],
               'o': [True, '']}

# RUNTIME OPTIONS
SWITCHES = {}
SOURCE_DIR = ""
EXPORT_DIR = ""
COMPACT_EXPORT = False

# VARS
# Slack data
users = []
users_map = {}
channels = []
channel_map = {}
channel_data = {}

# Export state
last_date = None
last_user = None

# FUNCS
# Loading
def loadJSONFile(file):
    loc = SOURCE_DIR + file

    log.log(logModes.HIGH, "Reading '" + loc + "'")

    file = open(loc, "r", encoding="utf8")
    data = file.read()
    data = json.loads(data)
    file.close()

    return data

def loadSlack():
    global users, users_map
    global channels, channel_map, channel_data

    print("Loading slack from: " + SOURCE_DIR)

    # Load channels and users
    channel_map = loadChannelMap()
    channels = sorted(channel_map.values())
    users_map = loadUserMapping()
    users = sorted(list(users_map.values()))

    if log.shouldLog(logModes.MEDIUM):
        print("Users and channels loaded")
        print("Loading channel data")

    # Load channel data
    for channel in channels:
        log.log(logModes.MEDIUM, "Loading channel data for #" + channel)
        channel_data[channel] = loadChannelData(channel)

    print("Slack loaded")

def loadChannelMap():
    channel_data = loadJSONFile("channels.json")

    # Build the array of channel names
    map = {}
    for i in channel_data:
        map[i['id']] = i['name']

    return map

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

        log.log(logModes.MEDIUM, "Exporting #" + channel + " to '" + loc + "'")

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
    formatted_data = []
    for msg in raw_json:
        formatted_data.append(formatMsgJSON(msg))
    formatted_data = "".join(formatted_data)

    return formatted_data.strip()

def formatMsgJSON(msg):
    global last_date, last_user

    prefix_str = "\n"

    # Get timestamp
    timestamp = msg['ts']
    dt = datetime.datetime.fromtimestamp(float(timestamp))
    date = dt.date()
    time = dt.time()

    # Denote change in date if new date
    if last_date == None or last_date < date:
        prefix_str += " -- " + str(date.day) + "/" + str(date.month) + "/" + str(date.year) + " -- \n"
        if not COMPACT_EXPORT:
            prefix_str = "\n" + prefix_str + "\n"

        last_date = date

    # Timestamp
    body_str = "[" + padInt(time.hour) + ":" + padInt(time.minute) + "] "

    # Get subtype and username
    subtype = None
    if 'subtype' in msg:
        subtype = msg['subtype']
    username = getUserName(msg)

    # If not compact and message is new (and date has not changed), add a newline to the prefix
    if not COMPACT_EXPORT and last_user != username and prefix_str == "\n":
        prefix_str = "\n" + prefix_str

    # Do stuff based on the subtype
    if subtype in SUBTYPES_IGNORE:
        return ""
    elif subtype in SUBTYPES_NO_PREFIX:
        body_str += formatMsgContents(msg, include_ampersand=False)
    elif subtype in SUBTYPES_REDUCED_PREFIX:
        body_str += username + " " + formatMsgContents(msg)
    elif subtype in SUBTYPES_CUSTOM:
        body_str += formatMsgContentsCustomType(msg, subtype, username)
    else:
        # Standard message
        # Do not process messages with thread_ts, they will either be processed by reply_broadcast or the parent message
        if 'thread_ts' in msg:
            return ""

        # If export mode is not compact, then display name if new user
        if COMPACT_EXPORT:
            body_str += username + ": "
        elif last_user != username:
            body_str = INDENTATION + username + ":\n" + body_str

        body_str += formatMsgContents(msg)

    # Update last_user
    last_user = username

    return prefix_str + body_str

def formatMsgContentsCustomType(msg, subtype, username):
    ret = ""

    if subtype == 'me_message':
        if COMPACT_EXPORT or last_user != username:
            ret += username + ": "
        ret += "_" + formatMsgContents(msg) + "_"

    elif subtype == 'reply_broadcast':
        ret += username + " replied to a thread"
        if 'plain_text' in msg:
            ret += ":\n" + INDENTATION + improveMsgContents(msg['plain_text'])

    return ret

def formatMsgContents(msg, include_ampersand=True):
    # If text is available (it sometimes might not be) then add it first
    # If attachments exist then add them
    ret_str = ""

    # Plain text
    if 'text' in msg:
        ret_str += improveMsgContents(msg['text'], include_ampersand)

    # Attachments
    if 'attachments' in msg:
        attachments = msg['attachments']

        for a in attachments:
            ret_str += formatMsgAttachment(a)

    # Last attachment should not add a newline, this is the easiest way to get rid of it
    if ret_str.endswith("\n"):
        ret_str = ret_str[:-1]

    return ret_str

def formatMsgAttachment(a):
    body_str = ""
    ret_str = ""

    # Only process attachments that contain at least 1 supported field
    if not any(field in ATTACHMENT_FIELDS for field in a):
        return body_str

    # Pretext should appear as standard text
    if 'pretext' in a:
        ret_str = improveMsgContents(a['pretext'])

    # Add title (include link if exists)
    title_str = ""
    if 'title_link' in a:
        title_str = "<" + a['title_link'] + ">"

        if 'title' in a:
            title_str = title_str[:-1] + "|" + a['title'] + ">"
    elif 'title' in a:
        title_str = a['title']

    if title_str != "":
        body_str += improveMsgContents(title_str)

        # Text isn't required, but it's highly likely
        if 'text' in a:
            body_str += "\n" + INDENTATION

    # Add text
    if 'text' in a:
        body_str += improveMsgContents(a['text'])

        if not COMPACT_EXPORT:
            body_str += "\n"

    # Add fields
    if 'fields' in a:
        # Remove the newline from the text in the attachment
        if body_str.endswith("\n"):
            body_str = body_str[:-1]

        # Combine fields
        fields = a['fields']
        field_str = ""
        for f in fields:
            if 'title' in f:
                field_str += f['title'] + "\n"

            field_str += f['value'] + "\n\n"
        field_str = field_str.strip()

        # Improve text and add to return string
        field_str = improveMsgContents(field_str)
        if body_str == "":
            body_str = field_str
        else:
            body_str += "\n\n" + INDENTATION + field_str

    # Denote the attachment by adding A: inline with the timestamp
    ret_str += "\n" + INDENTATION_SHORT + "A: " + body_str

    return ret_str

def improveMsgContents(msg: str, include_ampersand=True):
    # Make user and channel mentions readable
    msg = improveUserMentions(msg, include_ampersand)
    msg = improveChannelMentions(msg)

    # Replace HTML encoded characters
    for i in SLACK_HTML_ENCODING:
        msg = msg.replace(i, SLACK_HTML_ENCODING[i])

    # Improve indentation (use spaces instead of tabs, I expect most people to view the data using a monospaced font)
    # At least this works for notepad and notepad++
    msg = msg.replace("\n", "\n" + INDENTATION)

    return msg

def improveChannelMentions(msg: str):
    # Use regex to find channel mentions
    # Format 1, no pipe
    mentions = re.finditer('<#C([^|>]+)>', msg)
    for match in mentions:
        new_text = "#"
        id = match.group()[2:-1]

        if id in channel_map:
            new_text += channel_map[id]
        else:
            new_text += id

        msg = msg.replace(match.group(), new_text)

    # Format 2, pipe
    mentions = re.finditer('<#C([^|]+)[^>]+>', msg)
    for match in mentions:
        new_text = match.group()[2:-1]
        new_text = new_text.split("|")
        new_text = new_text[1]
        new_text = "#" + new_text

        msg = msg.replace(match.group(), new_text)

    return msg

def improveUserMentions(msg: str, include_ampersand=True):
    # Use regex to find user mentions
    # Format 1, no pipe
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

    # Format 2, pipe
    mentions = re.finditer('<@U([^|]+)[^>]+>', msg)
    for match in mentions:
        new_text = match.group()[2:-1]
        new_text = new_text.split("|")
        new_text = new_text[1]
        new_text = "@" + new_text

        msg = msg.replace(match.group(), new_text)

    return msg

def getUserName(msg):
    if 'user' in msg:
        username = msg['user']

        if username == "USLACKBOT":
            return 'Slackbot'
        else:
            return users_map[username]

    if 'username' in msg:
        username = msg['username']
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

def outputTypes():
    # On the test data set, only 'message' is contained, so this is fairly redundant atm
    types = set()

    print("Scanning history")
    for channel in channel_data:
        for message in channel_data[channel]:
            if "type" in message:
                types.add(message['type'])

    print("Types found in message history:")
    for i in sorted(types):
        print(i)

# Misc.
def padInt(val: int, length=2):
    ret = str(val)

    while len(ret) < length:
        ret = "0" + ret

    return ret

def strToBool(s: str):
    if s.upper() in TRUE_STRINGS:
        return True
    elif s.upper() in FALSE_STRINGS:
        return False
    else:
        print("Could not interpret '" + s + "' as boolean, assuming FALSE")
        return False

# Runtime
def loadArgs():
    interpretArgs(sys.argv)
    setSlackSource()
    setLogMode()
    setExportMode()

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
    if not 'l' in SWITCHES:
        return

    log.setModeStr(SWITCHES['l'])

def setExportLocation():
    global EXPORT_DIR

    if not 'o' in SWITCHES:
        return

    if SWITCHES['o'] == "":
        return

    EXPORT_DIR = SWITCHES['o']
    if not EXPORT_DIR.endswith("\\"):
        EXPORT_DIR += "\\"

def setExportMode():
    global COMPACT_EXPORT

    if not 'c' in SWITCHES:
        return

    COMPACT_EXPORT = strToBool(SWITCHES['c'])

# START OF PROGRAM
loadArgs()
loadSlack()
exportChosenOptions()