from tools.fablib import *

"""
Base configuration
"""
env.project_name = ''
env.file_path = '.'

# Environments
def production():
    """
    Work on production environment
    """
    env.settings = 'production'
    env.hosts = []
    env.user = ''
    env.password = ''


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
