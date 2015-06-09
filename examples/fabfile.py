from tools.fablib import *

from fabric.api import task


"""
Base configuration
"""
env.project_name = ''       # name for the project.
env.hosts = ['localhost', ]

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
    env.settings    = 'production'
    env.hosts       = []    # ssh host for production.
    env.user        = ''    # ssh user for production.
    env.password    = ''    # ssh password for production.


@task
def staging():
    """
    Work on staging environment
    """
    env.settings    = 'staging'
    env.hosts       = []    # ssh host for staging.
    env.user        = ''    # ssh user for staging.
    env.password    = ''    # ssh password for staging.

try:
    from local_fabfile import  *
except ImportError:
    pass
