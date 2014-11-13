from tools.fablib import *

from fabric.api import task


"""
Base configuration
"""
env.project_name = ''
env.file_path = '.'

"""
Add HipChat info to send a message to a room when new code has been deployed.
"""
env.hipchat_token = ''
env.hipchat_room_id = ''


# Environments
@task
def production():
    """
    Work on production environment
    """
    env.settings = 'production'
    env.hosts = []
    env.user = ''
    env.password = ''


@task
def staging():
    """
    Work on staging environment
    """
    env.settings = 'staging'
    env.hosts = []
    env.user = ''
    env.password = ''

try:
    from local_fabfile import  *
except ImportError:
    pass
