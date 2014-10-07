from fabric.api import *

from ..helpers import _create_db, _destroy_db, _load_db, _dump_db, _reload_db


# Local development helpers
env.vagrant_host = '192.168.33.10'
env.vagrant_db_user = 'root'
env.vagrant_db_pass = 'root'


def vagrant_create_db(name=None):
    """
    Create a new database on your vagrant instance
    """
    _create_db(name, env.vagrant_host, env.vagrant_db_user, env.vagrant_db_pass)


def vagrant_destroy_db(name=None):
    """
    Drop a database on your vagrant instance
    """
    _destroy_db(name, env.vagrant_host, env.vagrant_db_user, env.vagrant_db_pass)


def vagrant_load_db(dump=None, name=None):
    """
    Connects to your vagrant instance and loads the `vagrant` database with specified dump file
    """
    _load_db(dump, name, env.vagrant_host, env.vagrant_db_user, env.vagrant_db_pass)


def vagrant_dump_db(dump='vagrant_dump.sql', name=None):
    """
    Dump a database from your vagrant instance
    """
    _dump_db(dump, name, env.vagrant_host, env.vagrant_db_user, env.vagrant_db_pass)


def vagrant_reload_db(dump=None, name=None):
    """
    Destroy, create and load a database on your vagrant instance
    """
    _reload_db(dump, name, env.vagrant_host, env.vagrant_db_user, env.vagrant_db_pass)


def vagrant():
    """
    Work on vagrant (dev) environment
    """
    env.user = 'vagrant'
    env.hosts = [env.vagrant_host, ]
    env.path = '/vagrant'
    result = local('vagrant ssh-config | grep IdentityFile', capture=True)
    env.key_filename = result.split()[1]
