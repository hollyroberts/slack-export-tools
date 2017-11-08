from src.slack import *
import urllib.request

class avatars():
    IMAGE_SIZE_ORDER = ['original',
                        '512',
                        '192',
                        '72',
                        '48',
                        '32',
                        '24']

    def __init__(self, slack: slackData):
        self.slack = slack

    def exportAvatars(self, dir: str):
        log.log(logModes.LOW, "Downloading avatars")
        io.ensureDir(io.avatar_dir)

        for user_id in self.slack.metadata.users_json:
            user_json = self.slack.metadata.users_json[user_id]
            user_name = self.slack.metadata.users_map[user_id]

            if user_json['is_bot']:
                continue

            download_url = avatars.getLargestImage(user_json['profile'])
            if download_url == '':
                log.log(logModes.LOW, "Could not find an image for " + user_name)
                continue

            file_type = download_url.split('.')[-1]
            log.log(logModes.HIGH, "Downloading avatar for '" + user_name + "' from '" + download_url + "'")
            misc.download(download_url, io.avatar_dir + user_name + '.' + file_type)

    @staticmethod
    def getLargestImage(profile_json):
        for size in avatars.IMAGE_SIZE_ORDER:
            if 'image_' + size in profile_json:
                return profile_json['image_' + size]

        return ''