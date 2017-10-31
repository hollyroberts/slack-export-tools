import re

from src.misc import *
from src.slack import *

class exportModes(Enum):
    HTML = ".html"
    JSON = ".json"
    TEXT = ".txt"

class export():
    # CONSTANTS
    # Export settings, probably refactor
    COMPACT_EXPORT = False

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
                       'file_comment',
                       'file_mention',
                       'file_share',
                       'reply_broadcast')

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
    CHAR_PIPE = '|'

    HTML_DOC_START = "<!DOCTYPE html>\n<pre>"
    HTML_DOC_END = ""

    def __init__(self, slack_json):
        # Data
        self.slack = slack_json
        self.__currentChannel = None
        self.__last_date = None
        self.__last_user = None

        # Settings
        self.process_channel_threads = False

    def exportChannelData(self, folder_loc: str, mode: exportModes):
        print("Exporting channel data to '" + folder_loc + "'")

        io.ensureDir(folder_loc)

        for channel in self.slack.metadata.channels:
            self.__currentChannel = channel
            data = self.slack.channel_data[channel]

            loc = folder_loc + "#" + channel + mode.value
            log.log(logModes.MEDIUM, "Exporting #" + channel + " to '" + loc + "'")

            if mode is exportModes.HTML:
                data = self.formatChannelToHTML(data)
            if mode is exportModes.JSON:
                data = json.dumps(data, indent=4)
            elif mode is exportModes.TEXT:
                data = self.formatChannelToText(data)

            file = open(loc, "w", encoding="utf8")
            file.write(data)
            file.close()

            # Clear the record of progress
            self.__currentChannel = None

        print("Data exported")

    def formatChannelToHTML(self, raw_json):
        data = self.formatChannelToText(raw_json)
        #data = data.replace("\n", export.HTML_NEW_LINE)
        return export.HTML_DOC_START + data + export.HTML_DOC_END

    def formatChannelToText(self, raw_json, process_children=False):
        # Reset last date/user
        self.__last_date = None
        self.__last_user = None

        # Build and return data
        formatted_data = []
        for msg in raw_json:
            # Do not process thread child messages, they will either be processed by reply_broadcast or the parent message
            if not ('thread_ts' in msg and msg['thread_ts'] != msg['ts']) or process_children:
                formatted_data.append(self.__formatMsgJSON(msg))

        formatted_data = "".join(formatted_data)

        return formatted_data.strip()

    def __addAttachments(self, msg):
        ret_str = ""

        if 'attachments' in msg:
            attachments = msg['attachments']

            for a in attachments:
                ret_str += self.__formatMsgAttachment(a)

        # Last attachment should not add a newline, this is the easiest way to get rid of it
        if ret_str.endswith("\n"):
            ret_str = ret_str[:-1]

        return ret_str

    def __addThreadMsgs(self, parent):
        # Combine messages into array
        thread = []
        for child in parent['replies']:
            child_ts = child['ts']
            child_msg = self.slack.channel_threads[self.__currentChannel][child_ts]
            thread.append(child_msg)

        # Create a new export object to format the messages for us
        e = export(self.slack)
        e.process_channel_threads = True
        thread_str = e.formatChannelToText(thread, process_children=True)

        # Strip thread_str of leading/trailing whitespace, and add extra indentation
        thread_str = thread_str.strip()
        thread_str = thread_str.replace("\n", "\n" + export.INDENTATION_SHORT + export.CHAR_PIPE + "  ")

        return thread_str

    def __formatMsgJSON(self, msg):
        prefix_str = "\n"

        # Get timestamp
        timestamp = msg['ts']
        dt = datetime.datetime.fromtimestamp(float(timestamp))
        date = dt.date()
        time = dt.time()

        # Denote change in date if new date
        if self.__last_date is None or self.__last_date < date:
            prefix_str += " -- " + str(date.day) + "/" + str(date.month) + "/" + str(date.year) + " -- \n"
            if not export.COMPACT_EXPORT:
                prefix_str = "\n" + prefix_str + "\n"

            self.__last_date = date

        # Timestamp
        body_str = "[" + misc.padInt(time.hour) + ":" + misc.padInt(time.minute) + "] "

        # Get subtype and username
        subtype = None
        if 'subtype' in msg:
            subtype = msg['subtype']
        username = self.slack.metadata.getUserName(msg)

        # If not compact and message is new (and date has not changed), add a newline to the prefix
        if not export.COMPACT_EXPORT and self.__last_user != username and prefix_str == "\n":
            prefix_str = "\n" + prefix_str

        # Do stuff based on the subtype
        if subtype == 'thread_broadcast' and not self.process_channel_threads:
            return ""

        if subtype in export.SUBTYPES_NO_PREFIX:
            body_str += self.__formatMsgContents(msg, include_ampersand=False)
        elif subtype in export.SUBTYPES_REDUCED_PREFIX:
            body_str += username + " " + self.__formatMsgContents(msg)
        elif subtype in export.SUBTYPES_CUSTOM:
            body_str += self.__formatMsgContentsCustomType(msg, subtype, username)
        else:
            # Standard message
            # If export mode is not compact, then display name if new user
            if export.COMPACT_EXPORT:
                body_str += username + ": "
            elif self.__last_user != username:
                body_str = export.INDENTATION + username + ":\n" + body_str

            body_str += self.__formatMsgContents(msg)

        # If message contains replies, then add them as a thread
        if 'thread_ts' in msg and 'replies' in msg and len(msg['replies']) > 0:
            if not export.COMPACT_EXPORT:
                body_str += "\n"
            body_str += "\n" + export.INDENTATION_SHORT + "T: "
            body_str += self. __addThreadMsgs(msg)

        # Update last_user
        self.__last_user = username

        return prefix_str + body_str

    def __formatMsgContentsCustomType(self, msg, subtype, username):
        ret = ""

        if subtype == 'me_message':
            if export.COMPACT_EXPORT or self.__last_user != username:
                ret += username + ": "
            ret += "_" + self.__formatMsgContents(msg) + "_"

        elif subtype == 'file_comment':
            comment_username = self.slack.metadata.getUserName(msg['comment'])
            ret += self.__formatFileMessage(msg, comment_username, "commented on")

            ret += "\n" + export.INDENTATION_SHORT + "C: "
            ret += msg['comment']['comment']

        elif subtype == 'file_mention':
            ret += self.__formatFileMessage(msg, username, "mentioned")

        elif subtype == 'file_share':
            # File can be null, if so then just mention
            if msg['file'] is None:
                return msg['text']

            # Is the user uploading the file or sharing it
            if msg['upload']:
                ret += username + " uploaded a file: " + self.__getFileLink(msg)
                if 'initial_comment' in msg['file']:
                    ret += " and commented on it\n"
                    ret += export.INDENTATION_SHORT + "C: " + msg['file']['initial_comment']['comment']
            else:
                ret += self.__formatFileMessage(msg, username, "shared")

        elif subtype == 'reply_broadcast':
            ret += username + " replied to a thread"
            #if 'plain_text' in msg:
            #    ret += ":\n" + export.INDENTATION + self.__improveMsgContents(msg['plain_text'])
            ret += self.__addAttachments(msg)

        return ret

    def __formatFileMessage(self, msg, username, phrase: str):
        file_username = self.slack.metadata.getUserName(msg['file'])

        if file_username == username:
            return username + " " + phrase + " their file: " + self.__getFileLink(msg)
        else:
            return username + " " + phrase + " " + file_username + "'s file: " + self.__getFileLink(msg)

    def __formatMsgContents(self, msg, include_ampersand=True):
        ret_str = ""

        # Plain text
        if 'text' in msg:
            ret_str += self.__improveMsgContents(msg['text'], include_ampersand)

        # Attachments
        ret_str += self.__addAttachments(msg)

        return ret_str

    def __formatMsgAttachment(self, a):
        body_str = ""
        ret_str = ""

        # Only process attachments that contain at least 1 supported field
        if not any(field in export.ATTACHMENT_FIELDS for field in a):
            return body_str

        # Pretext should appear as standard text
        if 'pretext' in a:
            ret_str = self.__improveMsgContents(a['pretext'])

        # Add title (include link if exists)
        title_str = ""
        if 'title_link' in a:
            title_str = "<" + a['title_link'] + ">"

            if 'title' in a:
                title_str = title_str[:-1] + "|" + a['title'] + ">"
        elif 'title' in a:
            title_str = a['title']

        if title_str != "":
            body_str += self.__improveMsgContents(title_str)

            # Text isn't required, but it's highly likely
            if 'text' in a:
                body_str += "\n" + export.INDENTATION

        # Add text
        if 'text' in a:
            body_str += self.__improveMsgContents(a['text'])

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
            field_str = self.__improveMsgContents(field_str)
            if body_str == "":
                body_str = field_str
            else:
                body_str += "\n\n" + export.INDENTATION + field_str

        # Denote the attachment by adding A: inline with the timestamp
        ret_str += "\n" + export.INDENTATION_SHORT + "A: " + body_str

        return ret_str

    def __getFileLink(self, msg):
        ret_str = "<"

        if 'file' in msg:
            file_json = msg['file']

            if 'permalink' in file_json:
                ret_str += file_json['permalink']

            ret_str += "|"

            if 'name' in file_json:
                ret_str += file_json['name']

        ret_str += ">"
        return ret_str

    def __improveMsgContents(self, msg: str, include_ampersand=True):
        # Make user and channel mentions readable
        msg = self.__improveUserMentions(msg, include_ampersand)
        msg = self.__improveChannelMentions(msg)

        # Replace HTML encoded characters
        for i in export.SLACK_HTML_ENCODING:
            msg = msg.replace(i, export.SLACK_HTML_ENCODING[i])

        # Improve indentation (use spaces instead of tabs, I expect most people to view the data using a monospaced font)
        # At least this works for notepad and notepad++
        msg = msg.replace("\n", "\n" + export.INDENTATION)

        return msg

    def __improveChannelMentions(self, msg: str):
        # Use regex to find channel mentions
        # Format 1, no pipe
        mentions = re.finditer('<#C([^|>]+)>', msg)
        for match in mentions:
            new_text = "#"
            id = match.group()[2:-1]

            if id in self.slack.metadata.channel_map:
                new_text += self.slack.metadata.channel_map[id]
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

    def __improveUserMentions(self, msg: str, include_ampersand=True):
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
            elif ID in self.slack.metadata.users_map:
                new_text += self.slack.metadata.users_map[ID]
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