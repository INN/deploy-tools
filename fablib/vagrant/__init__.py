import os

from fabric.api import *
from fabric import colors
from fabric.contrib.console import confirm

from StringIO import StringIO

# Local development helpers
env.vagrant_host = '192.168.33.10'
env.vagrant_db_user = 'root'
env.vagrant_db_pass = 'root'


def vagrant_create_db(name=None):
    """
    Create a new database on your vagrant instance
    """
    env.vagrant_db_name = name or env.project_name

    print(colors.cyan("Creating database: %(vagrant_db_name)s" % env))
    local('mysql -s --host=%(vagrant_host)s --user=%(vagrant_db_user)s --password=%(vagrant_db_pass)s -e "create database %(vagrant_db_name)s;"' % env)
    print(colors.green('Finished creating database!'))


def vagrant_destroy_db(name=None):
    """
    Drop a database on your vagrant instance
    """
    if confirm(colors.red("Are you sure you want to destroy database: %s") % name):
        env.vagrant_db_name = name or env.project_name

        print(colors.red("Destroying database: %(vagrant_db_name)s" % env))
        local('mysql -s --host=%(vagrant_host)s --user=%(vagrant_db_user)s --password=%(vagrant_db_pass)s -e "drop database %(vagrant_db_name)s;"' % env)
        print(colors.green('Finished destroying database!'))
    else:
        print(colors.cyan("Exiting..."))
        exit()


def vagrant_load_db(dump=None, name=None):
    """
    Connects to your vagrant instance and loads the `vagrant` database with specified dump file
    """
    if dump:
        env.vagrant_db_name = name or env.project_name
        env.vagrant_dump_file = os.path.expanduser(dump)

        print(colors.cyan("Loading database..."))
        local('cat %(vagrant_dump_file)s | mysql -s --host=%(vagrant_host)s --user=%(vagrant_db_user)s --password=%(vagrant_db_pass)s %(vagrant_db_name)s' % env)
        print(colors.green('Finished loading database!'))
    else:
        print(colors.yellow('Please specify which database file to load!'))
        exit()


def vagrant_reload_db(dump=None, name=None):
    """
    Destroy, create and load a database on your vagrant instance
    """
    env.vagrant_db_name = name or env.project_name
    destroy_vagrant_db(env.vagrant_db_name)
    create_vagrant_db(env.vagrant_db_name)
    load_vagrant_db(dump, env.vagrant_db_name)
