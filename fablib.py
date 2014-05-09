import os
import glob

from datetime import datetime
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


def rollback():
    print(colors.red('Rolling back last deploy'))
    env.branch = 'rollback'


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

    if env.branch != 'rollback':
        local('git tag -f rollback')
        local('git fetch')

    print(colors.cyan("Checking out branch: %s" % env.branch))
    local('git checkout %s' % env.branch)

    print(colors.cyan("Initializing/updating git submodules..."))
    local('git submodule update --init --recursive')

    print(colors.cyan("Checking for uncommitted changes to the repo..."))
    _ensure_clean_repo()

    print(colors.cyan("Checking for untracked files to exclude..."))
    _ignore_untracked()

    print(colors.cyan("Using .gitignore file(s) to find files to exclude..."))
    _use_gitignore()

    env.sftp = _SFTP(env.host_string)

    with settings(warn_only=True):
        print(colors.cyan("Checking for eligible files and deploying..."))
        for f in _find_file_paths(env.file_path):
            if _check_last_modified(f):
                print(colors.green("Eligibile, deploying: %s" % f))
                result = put(local_path=f, remote_path='/%s' % f)
                if result.failed:
                    failed = result.failed[0]
                    new_dir = os.path.dirname(failed)

                    print(colors.yellow("Failed to transfer: %s" % failed))
                    print(colors.cyan("Creating new directory: %s" % new_dir))
                    env.sftp.mkdir(new_dir, False)

                    print(colors.cyan("Retrying transfer: %s" % failed))
                    put(local_path=f, remote_path='/%s' % f)
            else:
                print(colors.red("Not eligibile: %s" % f))


def _ensure_clean_repo():
    """
    Make sure there are no uncommitted changes being deployed.
    """
    result = local('git submodule foreach --recursive git ls-files --modified', capture=True)
    modified = [line for line in result.splitlines() if not line.startswith('Entering')]
    if modified:
        print(colors.red(
            "Found uncommitted changes in the repository or one of its submodules.\n"
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
            return False
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
    result = local('git submodule foreach --recursive git ls-files --others --exclude-standard', capture=True)
    untracked = [line for line in result.splitlines() if not line.startswith('Entering')]
    if untracked:
        for line in result.splitlines():
            env.ignore_files_containing.append(line)


def _use_gitignore():
    """
    Uses glob to find files that shouldn't be deployed based on your .gitignore file(s),
    adds them to `env.ignore_files_containing`.
    """
    ignore_files = local('find . -name ".gitignore" -print', capture=True)
    for file_path in ignore_files.splitlines():
        with open(file_path) as ignore_file:
            dir = os.path.dirname(file_path).replace('./', '')
            try:
                tests = [
                    "%s/%s" % (dir, line) for line in ignore_file.read().splitlines()
                    if not line.startswith('#') and line is not ''
                ]
                for test in tests:
                    env.ignore_files_containing = env.ignore_files_containing + glob.glob(test)
            except IOError:
                return False
