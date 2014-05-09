import os
import glob

from fabric.api import *
from fabric import colors
from fabric.sftp import SFTP as _SFTP

env.ignore_files_containing = ['.git', ]

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


def theme(name):
    """
    Specify a theme directory to deploy
    """
    env.file_path = 'wp-content/themes/%s/' % name


def deploy():
    """
    Deploy local copy of repository to target environment
    """
    require('settings', provided_by=["production", "staging", ])
    require('branch', provided_by=[master, stable, branch, ])

    local('git checkout %s' % env.branch)
    local('git submodule update --init --recursive')

    _ensure_clean_repo()
    _ignore_untracked()
    _use_gitignore()

    env.sftp = _SFTP(env.host_string)

    with settings(warn_only=True):
        for f in _find_file_paths(env.file_path):
            if _check_last_modified(f):
                result = put(local_path=f, remote_path='/%s' % f)
                if result.failed:
                    failed = result.failed[0]
                    new_dir = os.path.dirname(failed)

                    print(colors.yellow("Failed to transfer: %s" % failed))
                    print(colors.green("Creating new directory: %s" % new_dir))
                    env.sftp.mkdir(new_dir, False)

                    print(colors.green("Retrying transfer: %s" % failed))
                    put(local_path=f, remote_path='/%s' % f)


def _ensure_clean_repo():
    """
    Make sure there are no uncommitted changes being deployed.
    """
    modified = local('git ls-files --modified', capture=True)
    if modified:
        print(colors.red(
            "Found uncommitted changes in the repository.\n"
            "Please commit or stash your changes before deploying."))
        exit(1)


def _check_last_modified(file_path):
    """
    Check file last modified time to determine if it needs to be deployed.
    """
    transfer = True
    try:
        remote_last_modified = datetime.fromtimestamp(
            env.sftp.stat('/%s' % file_path).st_mtime)
        local_last_modified = datetime.fromtimestamp(
            os.stat(file_path).st_mtime)

        if local_last_modified <= remote_last_modified:
            transfer = False
    except IOError:
        pass
    return transfer


def _find_file_paths(directory):
    """
    A generator function that recursively finds all files for a given path.
    """
    for root, dirs, files in os.walk(directory):
        rel_path = os.path.relpath(root, directory)
        for f in files:
            # Skip dot files
            if f.startswith('.'):
                continue

            if rel_path == '.':
                one, two = f, os.path.join(root, f)
            else:
                one, two = os.path.join(rel_path, f), os.path.join(root, f)

            # Skip any files we explicitly say to ignore
            skip = False
            for s in env.ignore_files_containing:
                if s in one or s in two:
                    skip = True
                    break

            if skip:
                continue

            if env.file_path == '.':
                yield one
            else:
                yield two


def _ignore_untracked():
    """
    Grabs list of files that haven't been added to the git repo and
    adds them to `env.ignore_files_containing`.
    """
    result = local('git ls-files --others --exclude-standard', capture=True)
    if result:
        for line in result.splitlines():
            env.ignore_files_containing.append(line)


def _use_gitignore():
    """
    Uses glob to find files that shouldn't be deployed based on your .gitignore file,
    adds them to `env.ignore_files_containing`.
    """
    with open('.gitignore') as ignore_file:
        try:
            tests = [
                line for line in ignore_file.read().splitlines()
                if not line.startswith('#') and line is not ''
            ]
            for test in tests:
                env.ignore_files_containing = env.ignore_files_containing + glob.glob(test)
        except IOError:
            return False
