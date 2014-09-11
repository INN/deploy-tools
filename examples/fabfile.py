from tools.fablib import *

"""
Base configuration
"""
env.project_name = ''       # name for the project.
env.file_path = '.'         # path (relative to this file).

# Environments
def production():
    """
    Work on production environment
    """
    env.settings    = 'production'
    env.hosts       = []    # ssh host for production.
    env.user        = ''    # ssh user for production.
    env.password    = ''    # ssh password for production.


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