import os

from fabric.api import *
from fabric import colors


def search_replace(file=None, search=None, replacement="vagrant.dev"):
    """
    Search for and replace string in a file. Meant to be used with WP databases where
    one domain name needs to be replaced with another.

    Example:

        $ fab search_replace_domain:dump.sql,"inndev.wpengine.com","vagrant.dev"
    """
    file = os.path.expanduser(file)
    throwaway, ext = os.path.splitext(file)
    print(colors.cyan('Cleaning file. Searching for: %s, replacing with: %s' % (search, replacement)))
    local('cat %s | sed s/%s/%s/g > prepared%s' % (file, search, replacement, ext))
