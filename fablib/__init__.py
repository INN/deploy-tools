import os

from fabric.api import require, settings, task
from fabric.state import env
from fabric import colors, context_managers
from fabric.main import find_fabfile

# Other fabfiles
import local
import vagrant
import wp
import helpers
import assets

from hipchat import notify_hipchat
from helpers import capture

# Deployment related
env.path = ''
env.dry_run = False
env.verbose = False


@task
def stable():
    """
    Work on stable branch.
    """
    print(colors.green('On stable'))
    env.branch = 'stable'


@task
def master():
    """
    Work on development branch.
    """
    print(colors.yellow('On master'))
    env.branch = 'master'


@task
def branch(branch_name):
    """
    Work on any specified branch.
    """
    print(colors.red('On %s' % branch_name))
    env.branch = branch_name


@task
def rollback():
    """
    Deploy the most recent rollback point.
    """
    print(colors.red('Rolling back last deploy'))
    env.branch = 'rollback'


@task
def dry_run():
    """
    Don't transfer files, just output what would happen during a real deployment.
    """
    env.dry_run = True


@task
def verbose():
    """
    Show verbose output when running deploy commands
    """
    env.verbose = True


@task
def dev():
    """
    Work on development (vagrant) environment
    """
    env.user = 'vagrant'
    env.settings = 'vagrant'
    env.hosts = [env.vagrant_host, ]
    env.path = '/vagrant'
    result = capture('vagrant ssh-config | grep IdentityFile')
    env.key_filename = result.split()[1]


@task
def deploy():
    """
    Deploy local copy of repository to target environment.
    """
    require('branch', provided_by=[master, stable, branch, ])
    with context_managers.lcd(os.path.dirname(find_fabfile())): # Allows you to run deploy from any child directory of the project
        ret = wp.deploy()

    if ret.return_code and ret.return_code > 0:
        if ret.return_code in [4, ]:
            print(colors.red("Try running ") + colors.white("fab wp.verify_prerequisites"))
    else:
        notify_hipchat()
