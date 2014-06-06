from fabric.api import *

from ..helpers import _create_db, _destroy_db, _load_db, _dump_db, _reload_db


def local_create_db(name=None):
    """
    Create a new database on localhost
    """
    _create_db(name, '127.0.0.1', env.local_db_user, env.local_db_pass)

def local_destroy_db(name=None):
    """
    Drop a database on localhost
    """
    _destroy_db(name, '127.0.0.1', env.local_db_user, env.local_db_pass)


def local_load_db(dump=None, name=None):
    """
    Connects to your local mysql instance and loads the database with specified dump file
    """
    _load_db(dump, name, '127.0.0.1', env.local_db_user, env.local_db_pass)


def local_dump_db(dump='local_dump.sql', name=None):
    """
    Dump a database from localhost
    """
    _dump_db(dump, name, '127.0.0.1', env.local_db_user, env.local_db_pass)


def local_reload_db(dump=None, name=None):
    """
    Destroy, create and load a database on localhost
    """
    _reload_db(dump, name, '127.0.0.1', env.local_db_user, env.local_db_pass)
