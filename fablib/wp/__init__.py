import os

from fabric.api import local, require, settings, task, get, hide
from fabric.state import env
from fabric import colors

from ..helpers import capture

import cmd
import maintenance
import migrations
import tests

from StringIO import StringIO


@task
def verify_prerequisites():
    """
    Checks to make sure you have curl (with ssh) and git-ftp installed, Attempts installation via brew if you do not.
    """
    with settings(warn_only=True):

        print(colors.cyan("Verifying your installation of curl supports sftp..."))
        ret = capture('curl -V | grep sftp')
        if ret.return_code == 1:
            import sys
            if sys.platform.startswith('darwin'):
                print(colors.yellow(
                    'Your version of curl does not support sftp. Attempting installation of curl with sftp support via brew...'))
                capture('brew update')
                capture('brew install curl --with-ssh')
                capture('brew link --force curl')
            else:
                print(colors.red(
                    'Your version of curl does not support sftp. You may have to recompile it with sftp support. See the deploy-tools README for more information.'
                ))
        else:
            print(colors.green('Your installation of curl supports sftp!'))

        print(colors.cyan('Ensuring you have git-ftp installed...'))
        ret = capture('git ftp --version')
        if ret.return_code == 1:
            print(colors.yellow(
                'You do not have git-ftp installed. Attempting installation via brew...'))
            capture('brew update')
            capture('brew install git-ftp')
        else:
            print(colors.green('You have git-ftp installed!'))

        print(colors.green('Your system is ready to deploy code!'))


@task
def install(tag):
    """
    Downloads specified version of WordPress from https://github.com/WordPress/WordPress and
    installs it.
    """
    with settings(warn_only=True):
        try:
            print(colors.cyan('Downloading WordPress %s' % tag))
            capture('curl -L -O "https://github.com/WordPress/WordPress/archive/%s.zip"' % tag)

            print(colors.cyan('Unzipping...'))
            capture('unzip %s.zip' % tag)

            print(colors.cyan('Copying new files to our project directory...'))
            capture('rsync -ru WordPress-%s/* .' % tag)
        finally:
            print(colors.cyan('Cleaning up...'))
            capture('rm -Rf %s.zip' % tag)
            capture('rm -Rf WordPress-%s' % tag)

        print(colors.cyan('Finished upgrading WordPress!'))


@task
def fetch_sql_dump():
    """
    Gets the latest mysql.sql dump for your site from WPEngine.
    """
    print(colors.cyan("Fetching sql dump. This may take a while..."))
    get('wp-content/mysql.sql', 'mysql.sql')


# Utilities
def deploy():
    """
    Deploy local copy of repository to target WP Engine environment.
    """
    require('settings', provided_by=["production", "staging", ])

    if env.branch != 'rollback':
        rollback_sha1 = get_rollback_sha1()
        if rollback_sha1:
            print(colors.cyan("Setting rollback point..."))
            capture('git tag -af rollback %s -m "rollback tag"' % rollback_sha1)
            capture('git fetch')
        else:
            print(colors.yellow("No .git-ftp.log found on server. Unable to set rollback point."))

    print(colors.cyan("Checking out branch: %s" % env.branch))
    capture('git checkout %s' % env.branch)
    capture('git submodule update --init --recursive')

    with settings(warn_only=True):
        print(colors.cyan("Deploying..."))
        ret = do_deploy(env.path)

        if ret.return_code and ret.return_code > 0:
            if ret.return_code in [8, 5, ]:
                print(colors.cyan("Found no existing git repo on ftp host, initializing..."))
                ret = initial_deploy(env.path)
                if ret.return_code and ret.return_code > 0:
                    print(colors.red("An error occurred..."))
                    if not env.verbose:
                        print(colors.yellow('Try deploying with `verbose` for more information...'))
    return ret


def initial_deploy(dest_path):
    if env.dry_run:
        if env.verbose:
            cmd = 'git ftp init -v --dry-run --user "%s" --passwd "%s" sftp://%s:%s/%s' % (
                env.user, env.password, env.host_string, env.port, os.path.normpath(dest_path) + os.sep)
            with hide('running', 'warnings'):
                ret = local(cmd)
        else:
            cmd = 'git ftp init --dry-run --user "%s" --passwd "%s" sftp://%s:%s/%s' % (
                env.user, env.password, env.host_string, env.port, os.path.normpath(dest_path) + os.sep)
            with hide('running', 'stderr', 'warnings'):
                ret = local(cmd)
    else:
        if env.verbose:
            cmd = 'git ftp init -v --user "%s" --passwd "%s" sftp://%s:%s/%s' % (
                env.user, env.password, env.host_string, env.port, os.path.normpath(dest_path) + os.sep)
            with hide('running', 'warnings'):
                ret = local(cmd)
        else:
            cmd = 'git ftp init --user "%s" --passwd "%s" sftp://%s:%s/%s' % (
                env.user, env.password, env.host_string, env.port, os.path.normpath(dest_path) + os.sep)
            with hide('running', 'stderr', 'warnings'):
                ret = local(cmd)
    return ret


def do_deploy(dest_path):
    if env.dry_run:
        if env.verbose:
            cmd = 'git ftp push -v --dry-run --user "%s" --passwd "%s" sftp://%s:%s/%s' % (
                env.user, env.password, env.host_string, env.port, os.path.normpath(dest_path) + os.sep)
            with hide('running', 'warnings'):
                ret = local(cmd)
        else:
            cmd = 'git ftp push --dry-run --user "%s" --passwd "%s" sftp://%s:%s/%s' % (
                env.user, env.password, env.host_string, env.port, os.path.normpath(dest_path) + os.sep)
            with hide('running', 'stderr', 'warnings'):
                ret = local(cmd)
    else:
        if env.verbose:
            cmd = 'git ftp push -v --user "%s" --passwd "%s" sftp://%s:%s/%s' % (
                env.user, env.password, env.host_string, env.port, os.path.normpath(dest_path) + os.sep)
            with hide('running', 'warnings'):
                ret = local(cmd)
        else:
            cmd = 'git ftp push --user "%s" --passwd "%s" sftp://%s:%s/%s' % (
                env.user, env.password, env.host_string, env.port, os.path.normpath(dest_path) + os.sep)
            with hide('running', 'stderr', 'warnings'):
                ret = local(cmd)
    return ret


def get_rollback_sha1():
    with settings(warn_only=True):
        log_file = StringIO()
        get(remote_path='/.git-ftp.log', local_path=log_file)
        log_file.seek(0)
        try:
            rollback_commit = log_file.read().splitlines()[0]
        except IndexError:
            return None
        return rollback_commit
