import os
import sys

from fabric.api import local, require, settings, task, get, hide
from fabric.state import env
from fabric import colors

from ..helpers import capture

from StringIO import StringIO

import cmd
import maintenance
import tests
import blog

__all__ = [
    'verify_prerequisites',
    'install',
    'fetch_sql_dump',
    'deployed_commit',
    'cmd',
    'maintenance',
    'tests',
    'blog'
]

@task
def verify_prerequisites():
    """
    Checks to make sure you have curl (with ssh) and git-ftp installed, attempts installation via
    brew if you do not.
    """
    if env.get('sftp_deploy', False):
        print(colors.cyan("Verifying your installation of curl supports sftp..."))
        ret = capture('curl -V | grep sftp')
        if ret.return_code == 1:
            if sys.platform.startswith('darwin'):
                print(colors.yellow(
                    'Your version of curl does not support sftp. ' +
                    'Attempting installation of curl with sftp support via brew...'))
                capture('brew update')
                capture('brew install curl --with-ssh')
                capture('brew link --force curl')
            else:
                print(colors.red(
                    'Your version of curl does not support sftp. ' +
                    'You may have to recompile it with sftp support. ' +
                    'See the deploy-tools README for more information.'
                ))
        else:
            print(colors.green('Your installation of curl supports sftp!'))

        print(colors.cyan('Ensuring you have git-ftp installed...'))
        ret = capture('git ftp --version')
        if ret.return_code == 1:
            print(colors.red(
                'You do not have git-ftp installed!'))
            print(colors.yellow(
                """
                Install git-ftp version 0.9.0 using the instructions found here:
                https://github.com/git-ftp/git-ftp/blob/develop/INSTALL.md
                """))
            sys.exit(1)
        else:
            print(colors.green('You have git-ftp installed!'))
    else:
        print(colors.cyan("Verifying you have git installed..."))
        with settings(warn_only=True):
            ret = capture('git --version')
            if ret.return_code is not 0:
                print(colors.red("You do not have git installed or it is not properly configured."))
                sys.exit(1)

    print(colors.green('Your system is ready to deploy code!'))


@task
def install(tag='master'):
    """
    Downloads specified version of WordPress from https://github.com/WordPress/WordPress and
    installs it.
    """
    try:
        print(colors.cyan('Downloading WordPress %s' % tag))
        capture('curl -f -L -O "https://github.com/WordPress/WordPress/archive/%s.zip"' % tag)

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


def add_git_remote(environment=False):
    """
    Adds a WP Engine git remote based on the environment specified.
    """
    if not environment:
        print(colors.red(
            "You must specify an environment (production, staging) when adding a remote"))
        return False

    verbose = '--verbose ' if env.verbose else ''

    command = 'git remote %sadd %s git@git.wpengine.com:%s/%s.git' % (
        verbose,
        environment,
        environment,
        env.project_name
    )
    with hide('running', 'warnings'):
        print(colors.cyan('Adding remote for "%s"' % environment))
        ret = local(command)

    return ret


def remote_exists(environment=False):
    if not environment:
        print(colors.red(
            "You must specify an environment (production, staging) when adding a remote"))
        sys.exit(1)

    with settings(warn_only=True) and hide('running', 'stdout', 'stderr'):
        check_remotes = capture('git remote -v | grep -E "%s.*%s/%s.*$"' % (
            environment, environment, env.project_name))
        if check_remotes.return_code == 0:
            return True
        else:
            return False


# Utilities
def deploy():
    """
    Deploy local copy of repository to target WP Engine environment.
    """
    require('settings', provided_by=["production", "staging", ])

    if env.branch != 'rollback':
        rollback_sha1 = deployed_commit()

        if rollback_sha1:
            print(colors.cyan("Setting rollback point..."))
            capture('git tag -af rollback %s -m "rollback tag"' % rollback_sha1)
        else:
            print(colors.yellow("No rollback commit found. Unable to set rollback point."))

    if env.get('sftp_deploy', False):
        print(colors.cyan("Checking out branch: %s" % env.branch))
        capture('git checkout %s' % env.branch)
        capture('git submodule update --init --recursive')

    with settings(warn_only=True):
        print(colors.cyan("Deploying..."))

        if env.get('sftp_deploy', False):
            ret = do_sftp_deploy(env.path)

            if ret.return_code and ret.return_code > 0:
                if ret.return_code in [8, 5, ]:
                    print(colors.cyan("Found no existing git repo on ftp host, initializing..."))
                    ret = initial_deploy(env.path)
                    if ret.return_code and ret.return_code > 0:
                        print(colors.red("An error occurred..."))
                        if not env.verbose:
                            print(colors.yellow(
                                'Try deploying with `verbose` for more information...'))
        else:
            if not remote_exists(env.settings):
                added = add_git_remote(env.settings)
                if added.return_code is 0:
                    ret = do_git_deploy()
            else:
                ret = do_git_deploy()
    return ret


def initial_deploy(dest_path):
    dry_run = '--dry-run ' if env.dry_run else ''
    verbose = '--verbose ' if env.verbose else ''

    command = 'git ftp init %s%s--user "%s" --passwd "%s" sftp://%s:%s/%s' % (
        verbose,
        dry_run,
        env.user,
        env.password,
        env.host_string,
        env.port,
        os.path.normpath(dest_path) + os.sep
    )
    with hide('running', 'warnings'):
        ret = local(command)

    return ret


def do_sftp_deploy(dest_path):
    dry_run = '--dry-run ' if env.dry_run else ''
    verbose = '--verbose ' if env.verbose else ''

    command = 'git ftp push %s%s--user "%s" --passwd "%s" sftp://%s:%s/%s' % (
        verbose,
        dry_run,
        env.user,
        env.password,
        env.host_string,
        env.port,
        os.path.normpath(dest_path) + os.sep
    )
    with hide('running', 'warnings'):
        ret = local(command)

    return ret


def do_git_deploy():
    dry_run = '--dry-run ' if env.dry_run else ''
    verbose = '--verbose ' if env.verbose else ''

    command = 'git push %s%s%s %s:master' % (
        verbose,
        dry_run,
        env.settings,
        env.branch
    )

    with hide('running', 'warnings'):
        ret = local(command)

    return ret


@task()
def deployed_commit():
    """
    Retrieve the currently-deployed commit for an environment
    """
    require('settings', provided_by=["production", "staging", ])

    if env.get('sftp_deploy', False):
        commit_hash = get_sftp_rollback_sha1()
    else:
        commit_hash = get_rollback_sha1()

    print(colors.cyan("Currently-deployed commit: %s" % commit_hash))
    return commit_hash


def get_sftp_rollback_sha1():
    with settings(warn_only=True):
        log_file = StringIO()
        get(remote_path='/.git-ftp.log', local_path=log_file)
        log_file.seek(0)
        try:
            rollback_commit = log_file.read().splitlines()[0]
        except IndexError:
            return None
        return rollback_commit


def get_rollback_sha1():
    with settings(warn_only=True):
        rollback_commit = capture('git --no-pager log -n1 --pretty=format:"%H"')
        if rollback_commit.return_code == 0:
            return rollback_commit
        else:
            return None
