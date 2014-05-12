import os

from fabric.api import *
from fabric import colors
from fabric.contrib.console import confirm

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
    Specify the project's path on remote server
    """
    env.path = path


def dry_run():
    """
    Don't transfer files, just output what happen during a real deployment.
    """
    env.dry_run = True


def deploy():
    """
    Deploy local copy of repository to target environment
    """
    require('settings', provided_by=["production", "staging", ])
    require('branch', provided_by=[master, stable, branch, ])

    print(colors.cyan("Checking out branch: %s" % env.branch))
    local('git checkout %s' % env.branch)

    with settings(warn_only=True):
        print(colors.cyan("Deploying..."))
        ret = _deploy(env.path)

        if ret.return_code and ret.return_code > 0:
            if ret.return_code == 8:
                print(colors.cyan("Found no existing git repo on ftp host, initializing..."))
                _initial_deploy(env.path)

        if env.settings == 'production' and env.branch != 'rollback' and ret.return_code == 0:
            set_rollback_point()


def set_rollback_point():
    """
    Create a `rollback` tag and push to the remote.
    Deletes any existing `rollback` tag on the remote.
    """
    if confirm("Tag this release as a rollback point?"):
        print(colors.cyan("Tagging this release as a rollback point.."))

        with settings(warn_only=True):
            local('git push --delete origin rollback')

        local('git tag -f rollback')
        local('git push origin rollback')


def verify_prerequisites():
    """
    Checks to make sure you have curl (with ssh) and git-ftp installed, installs them if you do not.
    """
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


# Utilities
def _initial_deploy(dest_path):
    if env.dry_run:
            ret = local('git ftp init --dry-run --user %s --passwd %s sftp://%s/%s' % (
        env.user, env.password, env.host_string, os.path.normpath(dest_path) + os.sep), capture=True)
    else:
        ret = local('git ftp init --user %s --passwd %s sftp://%s/%s' % (
            env.user, env.password, env.host_string, os.path.normpath(dest_path) + os.sep), capture=True)
    return ret


def _deploy(dest_path):
    if env.dry_run:
        ret = local('git ftp push --dry-run --user %s --passwd %s sftp://%s/%s' % (
            env.user, env.password, env.host_string, os.path.normpath(dest_path) + os.sep), capture=True)
    else:
        ret = local('git ftp push --user %s --passwd %s sftp://%s/%s' % (
            env.user, env.password, env.host_string, os.path.normpath(dest_path) + os.sep), capture=True)
    return ret
