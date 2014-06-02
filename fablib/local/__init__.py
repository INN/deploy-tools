import os

from fabric.api import *
from fabric import colors
from fabric.contrib.console import confirm

from StringIO import StringIO


def local_create_db(name=None):
    """
    Create a new database on localhost
    """
    env.local_db_name = name or env.project_name

    print(colors.cyan("Creating database: %(local_db_name)s" % env))
    local('mysql -s --host=127.0.0.1 --user=%(local_db_user)s --password=%(local_db_pass)s -e "create database %(local_db_name)s;"' % env)
    print(colors.green('Finished creating database!'))


def local_destroy_db(name=None):
    """
    Drop a database on localhost
    """
    if confirm(colors.red("Are you sure you want to destroy database: %s") % name):
        env.local_db_name = name or env.project_name

        print(colors.red("Destroying database: %(local_db_name)s" % env))
        local('mysql -s --host=127.0.0.1 --user=%(local_db_user)s --password=%(local_db_pass)s -e "drop database %(local_db_name)s;"' % env)
        print(colors.green('Finished destroying database!'))
    else:
        print(colors.cyan("Exiting..."))
        exit()


def local_load_db(dump=None, name=None):
    """
    Connects to your local mysql instance and loads the database with specified dump file
    """
    if dump:
        env.local_db_name = name or env.project_name
        env.local_dump_file = os.path.expanduser(dump)

        print(colors.cyan("Loading database..."))
        local('cat %(local_dump_file)s | mysql -s --host=127.0.0.1 --user=%(local_db_user)s --password=%(local_db_pass)s %(local_db_name)s' % env)
        print(colors.green('Finished loading database!'))
    else:
        print(colors.yellow('Please specify which database file to load!'))
        exit()


def local_reload_db(dump=None, name=None):
    """
    Destroy, create and load a database on localhost
    """
    env.local_db_name = name or env.project_name
    destroy_local_db(env.local_db_name)
    create_local_db(env.local_db_name)
    load_local_db(dump, env.local_db_name)
