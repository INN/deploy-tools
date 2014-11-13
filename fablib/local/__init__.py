from fabric.api import task
from fabric.state import env

from .. import helpers

__all__ = ['create_db', 'destroy_db', 'load_db', 'dump_db', 'reload_db', ]


@task
def create_db(name=None):
    """
    Create a new database on localhost
    """
    helpers.create_db(name, '127.0.0.1', env.local_db_user, env.local_db_pass)


@task
def destroy_db(name=None):
    """
    Drop a database on localhost
    """
    helpers.destroy_db(name, '127.0.0.1', env.local_db_user, env.local_db_pass)


@task
def load_db(dump=None, name=None):
    """
    Connects to your local mysql instance and loads the database with specified dump file
    """
    helpers.load_db(dump, name, '127.0.0.1', env.local_db_user, env.local_db_pass)


@task
def dump_db(dump='local_dump.sql', name=None):
    """
    Dump a database from localhost
    """
    helpers.dump_db(dump, name, '127.0.0.1', env.local_db_user, env.local_db_pass)


@task
def reload_db(dump=None, name=None):
    """
    Destroy, create and load a database on localhost
    """
    helpers.reload_db(dump, name, '127.0.0.1', env.local_db_user, env.local_db_pass)
