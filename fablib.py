import os

from fabric.api import *
from fabric import colors
from fabric.contrib.console import confirm

env.path = ''

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


def install_prerequisites():
    """
    Install curl (with ssh) and git-ftp
    """
    local('brew update')
    local('brew install curl --with-ssh')
    local('brew link --force curl')
    local('brew install git-ftp')


# Utilities
def _initial_deploy(dest_path):
    ret = local('git ftp init --user %s --passwd %s sftp://%s/%s' % (
        env.user, env.password, env.host_string, os.path.normpath(dest_path) + os.sep), capture=True)
    return ret


def _deploy(dest_path):
    ret = local('git ftp push --user %s --passwd %s sftp://%s/%s' % (
        env.user, env.password, env.host_string, os.path.normpath(dest_path) + os.sep), capture=True)
    return ret
