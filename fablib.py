import os

from fabric.api import *
from fabric import colors
from fabric.contrib.console import confirm

from StringIO import StringIO

# Deployment related
env.path = ''
env.dry_run = False

def stable():
    """
    Work on stable branch.
    """
    print(colors.green('On stable'))
    env.branch = 'stable'


def master():
    """
    Work on development branch.
    """
    print(colors.yellow('On master'))
    env.branch = 'master'


def branch(branch_name):
    """
    Work on any specified branch.
    """
    print(colors.red('On %s' % branch_name))
    env.branch = branch_name


def rollback():
    """
    Deploy the most recent rollback point.
    """
    print(colors.red('Rolling back last deploy'))
    env.branch = 'rollback'


def path(path):
    """
    Specify the project's path on remote server.
    """
    env.path = path


def dry_run():
    """
    Don't transfer files, just output what would happen during a real deployment.
    """
    env.dry_run = True


def deploy():
    """
    Deploy local copy of repository to target environment.
    """
    require('settings', provided_by=["production", "staging", ])
    require('branch', provided_by=[master, stable, branch, ])

    if env.branch != 'rollback':
        rollback_sha1 = _get_rollback_sha1()
        if rollback_sha1:
            print(colors.cyan("Setting rollback point..."))
            local('git tag -af rollback %s -m "rollback tag"' % rollback_sha1)
            local('git fetch')
        else:
            print(colors.yellow("No .git-ftp.log found on server. Unable to set rollback point."))

    print(colors.cyan("Checking out branch: %s" % env.branch))
    local('git checkout %s' % env.branch)
    local('git submodule update --init --recursive')

    with settings(warn_only=True):
        print(colors.cyan("Deploying..."))
        ret = _deploy(env.path)

        if ret.return_code and ret.return_code > 0:
            if ret.return_code in [8, 5, ]:
                print(colors.cyan("Found no existing git repo on ftp host, initializing..."))
                _initial_deploy(env.path)


def verify_prerequisites():
    """
    Checks to make sure you have curl (with ssh) and git-ftp installed, installs them if you do not.
    """
    with settings(warn_only=True):
        local('brew update')

        print(colors.cyan("Verifying your installation of curl..."))
        ret = local('curl -V | grep sftp', capture=True)
        if ret.return_code == 1:
            print(colors.yellow(
                'Your version of curl does not support sftp. Installing curl with sftp support via brew...'))
            local('brew install curl --with-ssh')
            local('brew link --force curl')
        else:
            print(colors.green('Your installation of curl supports sftp!'))

        print(colors.cyan('Ensuring you have git-ftp installed...'))
        ret = local('git ftp --version', capture=True)
        if ret.return_code == 1:
            print(colors.yellow(
                'You don not have git-ftp installed. Installing...'))
            local('brew install git-ftp')
        else:
            print(colors.green('You have git-ftp installed!'))

        print(colors.green('Your system is ready to deploy code!'))


# Local development helpers
env.vagrant_host = '192.168.33.10'
env.vagrant_db_user = 'root'
env.vagrant_db_pass = 'root'

def upgrade_wordpress(tag):
    """
    Downloads specified version of WordPress from https://github.com/WordPress/WordPress and
    installs it.
    """
    with settings(warn_only=True):
        try:
            print(colors.cyan('Downloading WordPress %s' % tag))
            local('curl -L -O "https://github.com/WordPress/WordPress/archive/%s.zip"' % tag)

            print(colors.cyan('Unzipping...'))
            local('unzip %s.zip' % tag)

            print(colors.cyan('Copying new files to our project directory'))
            local('rsync -ru WordPress-%s/* .' % tag)
        finally:
            print(colors.cyan('Cleaning up...'))
            local('rm -Rf %s.zip' % tag)
            local('rm -Rf WordPress-%s' % tag)

        print(colors.cyan('Finished upgrading WordPress!'))


def search_replace_domain(dump=None, search=None, replacement="vagrant.dev"):
    """
    Search for and replace domain in a WordPress database dump

    Example:

        $ fab search_replace_domain:dump.sql,"inndev.wpengine.com"
    """
    dump = os.path.expanduser(dump)
    print(colors.cyan('Cleaning sql file. Searching for: %s, replacing with: %s' % (search, replacement)))
    local('cat %s | sed s/%s/%s/g > prepared.sql' % (dump, search, replacement))


def create_vagrant_db(name=None):
    """
    Create a new database on your vagrant instance
    """
    env.vagrant_db_name = name or env.project_name

    print(colors.cyan("Creating database: %(vagrant_db_name)s" % env))
    local('mysql -s --host=%(vagrant_host)s --user=%(vagrant_db_user)s --password=%(vagrant_db_pass)s -e "create database %(vagrant_db_name)s;"' % env)
    print(colors.green('Finished creating database!'))


def destroy_vagrant_db(name=None):
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


def load_vagrant_db(dump=None, name=None):
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


def reload_vagrant_db(dump=None, name=None):
    """
    Destroy, create and load a database on your vagrant instance
    """
    env.vagrant_db_name = name or env.project_name
    destroy_vagrant_db(env.vagrant_db_name)
    create_vagrant_db(env.vagrant_db_name)
    load_vagrant_db(dump, env.vagrant_db_name)


# Utilities
def _initial_deploy(dest_path):
    if env.dry_run:
        ret = local('git ftp init --dry-run --user "%s" --passwd "%s" sftp://%s/%s' % (
            env.user, env.password, env.host_string, os.path.normpath(dest_path) + os.sep))
    else:
        ret = local('git ftp init --user "%s" --passwd "%s" sftp://%s/%s' % (
            env.user, env.password, env.host_string, os.path.normpath(dest_path) + os.sep))
    return ret


def _deploy(dest_path):
    if env.dry_run:
        ret = local('git ftp push --dry-run --user "%s" --passwd "%s" sftp://%s/%s' % (
            env.user, env.password, env.host_string, os.path.normpath(dest_path) + os.sep))
    else:
        ret = local('git ftp push --user "%s" --passwd "%s" sftp://%s/%s' % (
            env.user, env.password, env.host_string, os.path.normpath(dest_path) + os.sep))
    return ret


def _get_rollback_sha1():
    with settings(warn_only=True):
        log_file = StringIO()
        get(remote_path='/.git-ftp.log', local_path=log_file)
        log_file.seek(0)
        try:
            rollback_commit = log_file.read().splitlines()[0]
        except IndexError:
            return None
        return rollback_commit
