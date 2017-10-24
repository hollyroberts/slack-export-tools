from src.export import *

# CONSTANTS
# Each switch maps to a boolean value, indicating whether or not data is required
# Default data is also contained for certain switches
SWITCH_CHAR = '-'
SWITCH_DATA = {'c': True,
               'i': True,
               'et': False,
               'ej': False,
               'eh': False,
               'l': True,
               'o': True,
               'os': True}
SWITCH_DEFAULT = {'et': "export_text",
                  'ej': "export_json",
                  'eh': "export_html"}

# Vars
switches = {}

# FUNCS

# Statistics (legacy code)
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
        for file in os.listdir(io.source_dir + channel):
            if file.endswith(".json"):
                # Process the file, get the scores for each user
                file_user_scores = calculateFileScores(channel + "\\" + file, users)

                # Update user_scores and channel_scores
                for username in file_user_scores:
                    user_scores[username] += file_user_scores[username]
                    channel_scores[channel] += file_user_scores[username]

    return user_scores, channel_scores

def calculateFileScores(file_loc, users):
    data = io.loadJSONFile(file_loc)
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
    e = export(slack)

    if 'et' in switches:
        e.exportChannelData(io.text_dir, exportModes.TEXT)

    if 'ej' in switches:
        e.exportChannelData(io.json_dir, exportModes.JSON)

    if 'eh' in switches:
        e.exportChannelData(io.html_dir, exportModes.HTML)

def calculateStatistics():
    pass

# Output info
def outputUsers():
    print("List of users:")
    for i in slack.users:
        print(i)

def outputSubtypes():
    subtypes = set()

    print("Scanning history")
    for channel in slack.channel_data:
        for message in slack.channel_data[channel]:
            if "subtype" in message:
                subtypes.add(message['subtype'])

    print("Subtypes found in message history:")
    for i in sorted(subtypes):
        print(i)

def outputTypes():
    # On the test data set, only 'message' is contained, so this is fairly redundant atm
    types = set()

    print("Scanning history")
    for channel in slack.channel_data:
        for message in slack.channel_data[channel]:
            if "type" in message:
                types.add(message['type'])

    print("Types found in message history:")
    for i in sorted(types):
        print(i)

# Runtime
def loadArgs():
    interpretArgs(sys.argv)
    setSlackSource()
    setLogMode()
    setExportMode()
    setExportLocations()

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
        if switch not in SWITCH_DATA:
            sys.exit("Incorrect args. Switch '" + switch + "' not found")

        # Switch must not have been added already
        if switch in switches:
            sys.exit("Incorrect args. Switch '" + switch + "' has already been added")

        # Does switch require an argument
        if SWITCH_DATA[switch]:
            i += 1
            if i >= len(argv):
                sys.exit("Incorrect args. Required an argument for '" + switch + "', but ran out of arguments")

            if argv[i].startswith(SWITCH_CHAR):
                sys.exit("Incorrect args. Required argument for '" + switch + "', but found a switch")

            switches[switch] = argv[i]
        else:
            i += 1

            # If there are no more arguments or next argument is a switch then either add none or the appropriate value
            if i >= len(argv) or argv[i].startswith(SWITCH_CHAR):
                if switch in SWITCH_DEFAULT:
                    switches[switch] = SWITCH_DEFAULT[switch]
                else:
                    switches[switch] = None
                continue

            switches[switch] = argv[i]

        i += 1

def setSlackSource():
    if 'i' not in switches or switches['i'] == "":
        source_dir = ""
    else:
        source_dir = switches['i']
        if not source_dir.endswith("\\"):
            source_dir += "\\"

    io.source_dir = source_dir

def setLogMode():
    if 'l' not in switches:
        return

    log.setModeStr(switches['l'])

def setExportLocations():
    io.setExportDir(switches.get('o', ""))
    io.setStatsDir(switches.get('os', "stats\\"))

    io.setHtmlDir(switches.get('eh', SWITCH_DEFAULT['eh']))
    io.setJsonDir(switches.get('ej', SWITCH_DEFAULT['ej']))
    io.setTextDir(switches.get('et', SWITCH_DEFAULT['et']))

def setExportMode():
    mode = False
    if 'c' in switches:
        mode = misc.strToBool(switches['c'])

    export.COMPACT_EXPORT = mode

# START OF PROGRAM
loadArgs()
slack = slackData()
exportChosenOptions()
calculateStatistics()