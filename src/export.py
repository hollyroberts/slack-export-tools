import os
import json
import datetime
import re

from src.log import *
from src.misc import *

class export():
    last_data = None
    last_user = None
    slack = None

    # Export settings, probably refactor
    COMPACT_EXPORT = False

    # Constants
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

    def __init__(self):
        pass

    @staticmethod
    def exportChannelData(slack, folder_loc: str, as_json=False):
        print("Exporting channel data to '" + folder_loc + "'")

        # Slack object to retrieve data from
        export.slack = slack

        if not os.path.exists(folder_loc):
            os.makedirs(folder_loc)

        for channel in slack.channels:
            data = slack.channel_data[channel]

            loc = folder_loc + "\\#" + channel
            if as_json:
                loc += ".json"
            else:
                loc += ".txt"

            log.log(logModes.MEDIUM, "Exporting #" + channel + " to '" + loc + "'")

            if as_json:
                data = json.dumps(data, indent=4)
            else:
                data = export.__formatChannelJSON(data)

            file = open(loc, "w", encoding="utf8")
            file.write(data)
            file.close()

        print("Data exported")

    @staticmethod
    def __formatChannelJSON(raw_json):
        # Reset last date/user
        export.last_date = None
        export.last_user = None

        # Build and return data
        formatted_data = []
        for msg in raw_json:
            formatted_data.append(export.__formatMsgJSON(msg))
        formatted_data = "".join(formatted_data)

        return formatted_data.strip()

    @staticmethod
    def __formatMsgJSON(msg):
        global last_date, last_user

        prefix_str = "\n"

        # Get timestamp
        timestamp = msg['ts']
        dt = datetime.datetime.fromtimestamp(float(timestamp))
        date = dt.date()
        time = dt.time()

        # Denote change in date if new date
        if export.last_date is None or export.last_date < date:
            prefix_str += " -- " + str(date.day) + "/" + str(date.month) + "/" + str(date.year) + " -- \n"
            if not export.COMPACT_EXPORT:
                prefix_str = "\n" + prefix_str + "\n"

            export.last_date = date

        # Timestamp
        body_str = "[" + misc.padInt(time.hour) + ":" + misc.padInt(time.minute) + "] "

        # Get subtype and username
        subtype = None
        if 'subtype' in msg:
            subtype = msg['subtype']
        username = export.slack.getUserName(msg)

        # If not compact and message is new (and date has not changed), add a newline to the prefix
        if not export.COMPACT_EXPORT and export.last_user != username and prefix_str == "\n":
            prefix_str = "\n" + prefix_str

        # Do stuff based on the subtype
        if subtype in export.SUBTYPES_IGNORE:
            return ""
        elif subtype in export.SUBTYPES_NO_PREFIX:
            body_str += export.__formatMsgContents(msg, include_ampersand=False)
        elif subtype in export.SUBTYPES_REDUCED_PREFIX:
            body_str += username + " " + export.__formatMsgContents(msg)
        elif subtype in export.SUBTYPES_CUSTOM:
            body_str += export.__formatMsgContentsCustomType(msg, subtype, username)
        else:
            # Standard message
            # Do not process messages with thread_ts, they will either be processed by reply_broadcast or the parent message
            if 'thread_ts' in msg:
                return ""

            # If export mode is not compact, then display name if new user
            if export.COMPACT_EXPORT:
                body_str += username + ": "
            elif export.last_user != username:
                body_str = export.INDENTATION + username + ":\n" + body_str

            body_str += export.__formatMsgContents(msg)

        # Update last_user
        export.last_user = username

        return prefix_str + body_str

    @staticmethod
    def __formatMsgContentsCustomType(msg, subtype, username):
        ret = ""

        if subtype == 'me_message':
            if export.COMPACT_EXPORT or export.last_user != username:
                ret += username + ": "
            ret += "_" + export.__formatMsgContents(msg) + "_"

        elif subtype == 'reply_broadcast':
            ret += username + " replied to a thread"
            if 'plain_text' in msg:
                ret += ":\n" + export.INDENTATION + export.__improveMsgContents(msg['plain_text'])

        return ret

    @staticmethod
    def __formatMsgContents(msg, include_ampersand=True):
        # If text is available (it sometimes might not be) then add it first
        # If attachments exist then add them
        ret_str = ""

        # Plain text
        if 'text' in msg:
            ret_str += export.__improveMsgContents(msg['text'], include_ampersand)

        # Attachments
        if 'attachments' in msg:
            attachments = msg['attachments']

            for a in attachments:
                ret_str += export.__formatMsgAttachment(a)

        # Last attachment should not add a newline, this is the easiest way to get rid of it
        if ret_str.endswith("\n"):
            ret_str = ret_str[:-1]

        return ret_str

    @staticmethod
    def __formatMsgAttachment(a):
        body_str = ""
        ret_str = ""

        # Only process attachments that contain at least 1 supported field
        if not any(field in export.ATTACHMENT_FIELDS for field in a):
            return body_str

        # Pretext should appear as standard text
        if 'pretext' in a:
            ret_str = export.__improveMsgContents(a['pretext'])

        # Add title (include link if exists)
        title_str = ""
        if 'title_link' in a:
            title_str = "<" + a['title_link'] + ">"

            if 'title' in a:
                title_str = title_str[:-1] + "|" + a['title'] + ">"
        elif 'title' in a:
            title_str = a['title']

        if title_str != "":
            body_str += export.__improveMsgContents(title_str)

            # Text isn't required, but it's highly likely
            if 'text' in a:
                body_str += "\n" + export.INDENTATION

        # Add text
        if 'text' in a:
            body_str += export.__improveMsgContents(a['text'])

            if not export.COMPACT_EXPORT:
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
            field_str = export.__improveMsgContents(field_str)
            if body_str == "":
                body_str = field_str
            else:
                body_str += "\n\n" + export.INDENTATION + field_str

        # Denote the attachment by adding A: inline with the timestamp
        ret_str += "\n" + export.INDENTATION_SHORT + "A: " + body_str

        return ret_str

    @staticmethod
    def __improveMsgContents(msg: str, include_ampersand=True):
        # Make user and channel mentions readable
        msg = export.__improveUserMentions(msg, include_ampersand)
        msg = export.__improveChannelMentions(msg)

        # Replace HTML encoded characters
        for i in export.SLACK_HTML_ENCODING:
            msg = msg.replace(i, export.SLACK_HTML_ENCODING[i])

        # Improve indentation (use spaces instead of tabs, I expect most people to view the data using a monospaced font)
        # At least this works for notepad and notepad++
        msg = msg.replace("\n", "\n" + export.INDENTATION)

        return msg

    @staticmethod
    def __improveChannelMentions(msg: str):
        # Use regex to find channel mentions
        # Format 1, no pipe
        mentions = re.finditer('<#C([^|>]+)>', msg)
        for match in mentions:
            new_text = "#"
            id = match.group()[2:-1]

            if id in export.slack.channel_map:
                new_text += export.slack.channel_map[id]
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

    @staticmethod
    def __improveUserMentions(msg: str, include_ampersand=True):
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
            elif ID in export.slack.users_map:
                new_text += export.slack.users_map[ID]
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