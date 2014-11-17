from fabric.api import task
from fabric.state import env

from .. import helpers

__all__ = ['create_db', 'destroy_db', 'load_db', 'dump_db', 'reload_db', 'vagrant', ]

# Local development helpers
env.vagrant_host = '192.168.33.10'
env.vagrant_db_user = 'root'
env.vagrant_db_pass = 'root'


@task
def create_db(name=None):
    """
    Create a new database on your vagrant instance
    """
    helpers.create_db(name, env.vagrant_host, env.vagrant_db_user, env.vagrant_db_pass)


@task
def destroy_db(name=None):
    """
    Drop a database on your vagrant instance
    """
    helpers.destroy_db(name, env.vagrant_host, env.vagrant_db_user, env.vagrant_db_pass)


@task
def load_db(dump=None, name=None):
    """
    Connects to your vagrant instance and loads the `vagrant` database with specified dump file
    """
    helpers.load_db(dump, name, env.vagrant_host, env.vagrant_db_user, env.vagrant_db_pass)


@task
def dump_db(dump='vagrant_dump.sql', name=None):
    """
    Dump a database from your vagrant instance
    """
    helpers.dump_db(dump, name, env.vagrant_host, env.vagrant_db_user, env.vagrant_db_pass)


@task
def reload_db(dump=None, name=None):
    """
    Destroy, create and load a database on your vagrant instance
    """
    helpers.reload_db(dump, name, env.vagrant_host, env.vagrant_db_user, env.vagrant_db_pass)
