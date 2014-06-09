import os

from fabric.api import *
from fabric import colors

from StringIO import StringIO


def deploy():
    """
    Deploy local copy of repository to target WP Engine environment.
    """
    require('settings', provided_by=["production", "staging", ])

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
    Checks to make sure you have curl (with ssh) and git-ftp installed, Attempts installation via brew if you do not.
    """
    with settings(warn_only=True):

        print(colors.cyan("Verifying your installation of curl supports sftp..."))
        ret = local('curl -V | grep sftp', capture=True)
        if ret.return_code == 1:
            print(colors.yellow(
                'Your version of curl does not support sftp. Attempting installation of curl with sftp support via brew...'))
            local('brew update')
            local('brew install curl --with-ssh')
            local('brew link --force curl')
        else:
            print(colors.green('Your installation of curl supports sftp!'))

        print(colors.cyan('Ensuring you have git-ftp installed...'))
        ret = local('git ftp --version', capture=True)
        if ret.return_code == 1:
            print(colors.yellow(
                'You do not have git-ftp installed. Attempting installation via brew...'))
            local('brew update')
            local('brew install git-ftp')
        else:
            print(colors.green('You have git-ftp installed!'))

        print(colors.green('Your system is ready to deploy code!'))


def install_wordpress(tag):
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

            print(colors.cyan('Copying new files to our project directory...'))
            local('rsync -ru WordPress-%s/* .' % tag)
        finally:
            print(colors.cyan('Cleaning up...'))
            local('rm -Rf %s.zip' % tag)
            local('rm -Rf WordPress-%s' % tag)

        print(colors.cyan('Finished upgrading WordPress!'))


def fetch_sql_dump():
    """
    Gets the latest mysql.sql dump for your site from WPEngine.
    """
    print(colors.cyan("Fetching sql dump. This may take a while..."))
    get('wp-content/mysql.sql', 'mysql.sql')


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
