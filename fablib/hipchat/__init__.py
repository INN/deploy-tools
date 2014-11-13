import json

from fabric.state import env

from urllib import urlopen, urlencode

from .. import helpers

__all__ = ['notify_hipchat', 'HipChatNotifier', ]


class HipChatNotifier:

    base_url = 'https://api.hipchat.com/v1/'

    def __init__(self, token=None, *args, **kwargs):
        self.token = token
        self.base_params = '?format=json&auth_token=' + self.token

    def message(self, room_id=None, fromName=None, message=None, notify=False, color='yellow'):
        url = self.base_url + 'rooms/message' + self.base_params
        data = {
            'room_id': room_id,
            'message': message,
            'from': fromName,
            'notify': notify,
            'color': color,
        }
        ret = urlopen(url, urlencode(data))
        return json.loads(ret.read())

    def topic(self, room_id=None, topic=None, fromName=None):
        url = self.base_url + 'rooms/topic' + self.base_params
        data = {
            'room_id': room_id,
            'topic': topic,
            'from': fromName,
        }
        ret = urlopen(url, urlencode(data))
        return json.loads(ret.read())


def notify_hipchat():
    """
    Send notification to a HipChat room
    """
    if env.hipchat_token and env.hipchat_room_id and not env.dry_run:
        hp = HipChatNotifier(env.hipchat_token)
        name = helpers.capture('git config user.name')
        if name is '':
            name = 'Someone'
        message = '%s just deployed "%s" (branch: %s) to %s' % (name, env.project_name, env.branch, env.settings)
        hp.message(env.hipchat_room_id, 'Deployment', message, True)
