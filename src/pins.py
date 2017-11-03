from src.slack import *

class pins():
    def __init__(self, slack: slackData):
        self.slack = slack

    def export(self, dir: str):
        for channel_id in self.slack.metadata.channel_map.keys():
            current_pins = self.currentPins(channel_id, self.slack.metadata.channels_json[channel_id])

    def currentPins(self, channel_id, channel_json):
        # Make sure there are pins
        if 'pins' not in channel_json:
            return []

        # Vars
        channel_name = self.slack.metadata.channel_map[channel_id]
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
                    pins.append(x)
                    found_pin = True
                    break

            if not found_pin:
                pins_not_found += 1
                log.log(logModes.MEDIUM, "Could not find pin with id/ts '" + pin['id'] + "' in #" + channel_name)

        if pins_not_found > 0:
            log.log(logModes.LOW, "Could not find " + str(pins_not_found) + " pin(s) for #" + channel_name)

        return pins