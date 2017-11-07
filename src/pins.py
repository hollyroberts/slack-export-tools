from src.export import *

class pins():
    def __init__(self, slack: slackData):
        self.slack = slack

    def export(self, dir: str):
        for channel_id in self.slack.metadata.channel_map.keys():
            channel_name = self.slack.metadata.channel_map[channel_id]

            # Get pins to varying degrees
            current_pins = self.currentPins(channel_name, self.slack.metadata.channels_json[channel_id])

            # Output the pins
            self.exportPins(io.pins_dir + "current\\", channel_name, current_pins)

        log.log(logModes.LOW, "Exported pin data to '" + io.pins_dir + "'")

    def exportPins(self, dir: str, channel:str, pins):
        out_str = ""
        counter = 0
        for i in pins:
            pin = i[0]
            msg = i[1]
            counter += 1

            # User is the one that pinned the
            out_str += "Pin #" + str(counter) + " pinned by " + self.slack.metadata.users_map[pin['user']] + "\n"
            out_str += export.formatTimestamp(msg['ts'], full=True) + "\n"
            out_str += self.slack.metadata.getUserName(msg) + ": " + msg['text'] + "\n"
            out_str += "\n------------------------------------------------------------------\n\n"

        io.ensureDir(dir)
        file = open(dir + "#" + channel + ".txt", "w", encoding="utf8")
        file.write(out_str)
        file.close()

    def currentPins(self, channel_name, channel_json):
        # Make sure there are pins
        if 'pins' not in channel_json:
            return []

        # Vars
        pins_not_found = 0
        pins = []

        # Iterate over pins, attempt to find corresponding message
        for pin in channel_json['pins']:
            found_pin = False

            # ATM only support message pins TODO add support for more file types
            if pin['type'] != 'C':
                continue

            # Search through channel messages
            for x in self.slack.channel_data[channel_name]:
                if x['ts'] == pin['id']:
                    pins.append([pin, x])
                    found_pin = True
                    break

            if not found_pin:
                pins_not_found += 1
                log.log(logModes.MEDIUM, "Could not find pin with id/ts '" + pin['id'] + "' in #" + channel_name)

        if pins_not_found > 0:
            log.log(logModes.LOW, "Could not find " + str(pins_not_found) + " pin(s) for #" + channel_name)

        return pins