import os

from fabric.api import local, task, hide, run, sudo
from fabric.state import env
from fabric import colors
from fabric.contrib.console import confirm


# Database utilities
@task(alias='sr')
def search_replace(file=None, search=None, replacement="vagrant.dev"):
    """
    Search for and replace string in a file. Meant to be used with WP databases where
    one domain name needs to be replaced with another.

    Example:

        $ fab search_replace:dump.sql,"inndev.wpengine.com","vagrant.dev"
    """
    file = os.path.expanduser(file)
    throwaway, ext = os.path.splitext(file)
    with hide('running', 'stdout', 'stderr'):
        print(colors.cyan('Cleaning file. Searching for: %s, replacing with: %s' % (search, replacement)))
        local('cat %s | sed "s/%s/%s/g" > prepared%s' % (file, search, replacement, ext))


def create_db(name=None, host=None, user=None, password=None):
    """
    Create a new database
    """
    if None in [host, user, password]:
        raise ValueError('Must specifiy database host, user and password')

    require_env_var('project_name')

    env.db_host = host
    env.db_user = user
    env.db_pass = password
    env.db_name = name or env.project_name

    with hide('running', 'stdout', 'stderr'):
        print(colors.cyan("Creating database: %(db_name)s" % env))
        local('mysql -s --host=%(db_host)s --user=%(db_user)s --password=%(db_pass)s -e "create database %(db_name)s;"' % env)
        print(colors.green('Finished creating database!'))


def destroy_db(name=None, host=None, user=None, password=None):
    """
    Drop a database
    """
    if None in [host, user, password]:
        raise ValueError('Must specifiy database host, user and password')

    require_env_var('project_name')

    if confirm(colors.red("Are you sure you want to destroy database: %s") % name):
        env.db_host = host
        env.db_user = user
        env.db_pass = password
        env.db_name = name or env.project_name

        with hide('running', 'stdout', 'stderr'):
            print(colors.red("Destroying database: %(db_name)s" % env))
            local('mysql -s --host=%(db_host)s --user=%(db_user)s --password=%(db_pass)s -e "drop database %(db_name)s;"' % env)
            print(colors.green('Finished destroying database!'))
    else:
        print(colors.cyan("Exiting..."))
        exit()


def load_db(dump=None, name=None, host=None, user=None, password=None):
    """
    Load a database with specified dump file
    """
    if None in [host, user, password]:
        raise ValueError('Must specifiy database host, user and password')

    require_env_var('project_name')

    if dump:
        env.db_host = host
        env.db_user = user
        env.db_pass = password
        env.db_name = name or env.project_name
        env.dump_file = os.path.expanduser(dump)

        with hide('running', 'stdout', 'stderr'):
            print(colors.cyan("Loading database..."))
            local('cat %(dump_file)s | mysql -s --host=%(db_host)s --user=%(db_user)s --password=%(db_pass)s %(db_name)s' % env)
            print(colors.green('Finished loading database!'))
    else:
        print(colors.yellow('Please specify which database file to load!'))
        exit()


def dump_db(dump='dump.sql', name=None, host=None, user=None, password=None):
    """
    Dump a database
    """
    if None in [host, user, password]:
        raise ValueError('Must specifiy database host, user and password')

    require_env_var('project_name')

    env.db_host = host
    env.db_user = user
    env.db_pass = password
    env.db_name = name or env.project_name
    env.dump_file = os.path.expanduser(dump)

    with hide('running', 'stdout', 'stderr'):
        print(colors.cyan('Dumping database: %(db_name)s' % env))
        local('mysqldump -h %(db_host)s -u %(db_user)s -p%(db_pass)s --quick %(db_name)s > %(dump_file)s' % env)
        print(colors.green('Finished dumping database!'))


def reload_db(dump=None, name=None, host=None, user=None, password=None):
    """
    Destroy, create and load a database
    """
    destroy_db(name or env.project_name, host, user, password)
    create_db(name or env.project_name, host, user, password)
    load_db(dump, name or env.project_name, host, user, password)


def require_env_var(name):
    """
    Be sure that an env variable is defined and that it is not an empty string
    """
    error = ValueError('Required environment variable `project_name` can not be empty or None')
    try:
        ret = getattr(env, name)
        if ret is '':
            raise error
    except AttributeError:
        raise error


def capture(cmd, cmd_type='local'):
    """
    Capture output of a command and suppress messages that Fabric is
    running the command. (e.g. "[hostname] run: ...")
    """
    with hide('running', 'stdout'):
        if cmd_type is 'local':
            result = local(cmd, capture=True)
        if cmd_type is 'run':
            result = run(cmd)
        if cmd_type is 'sudo':
            result = sudo(cmd)
        return result
