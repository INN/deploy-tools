import json

from fabric.api import cd, hide, put, require, run as run_cmd, settings, shell_env, sudo, task
from fabric.state import env
from fabric import colors

from .. import helpers
from .. import vagrant

from StringIO import StringIO

__all__ = ['setup', 'run', 'install_phpunit', ]

WP_TEST_DB = 'largotest'
WP_TESTS_DIR = '/tmp/wordpress-tests-lib'
WP_CORE_DIR = '/vagrant/'
WP_VERSION = '3.9.1'


@task
def setup(name):
    """
    Setup unit tests for a theme or plugin
    """
    require('settings', provided_by=['vagrant', ])

    print(colors.cyan("Setting up tests for " + name + "..."))

    # Does this theme or plugin exist?
    with cd(env.path):
        plugins = json.loads(helpers.capture('wp plugin list --format=json --fields=name', cmd_type='run'))
        themes = json.loads(helpers.capture('wp theme list --format=json --fields=name', cmd_type='run'))

        test = { 'name': name }
        if test in plugins:
            print "Found plugin: " + name
            print "Initalizing tests..."

            directory = get_path('plugin', name)
            scaffold_tests(directory)
        elif test in themes:
            print "Found theme: " + name
            print "Initalizing tests..."

            directory = get_path('theme', name)
            scaffold_tests(directory)
        else:
          print "Warning: Could not find theme or plugin: " + colors.red(name)


@task
def run(name):
    """
    Run unit tests for a theme or plugin
    """
    require('settings', provided_by=['vagrant', ])

    with cd(env.path):
        plugins = json.loads(helpers.capture('wp plugin list --format=json --fields=name', cmd_type='run'))
        themes = json.loads(helpers.capture('wp theme list --format=json --fields=name', cmd_type='run'))

        test = { 'name': name }
        if test in plugins:
            directory = get_path('plugin', name)
        elif test in themes:
            directory = get_path('theme', name)

    shell_env_vars = {
        'WP_TESTS_DIR': WP_TESTS_DIR,
        'WP_CORE_DIR': WP_CORE_DIR
    }
    with cd(directory), shell_env(**shell_env_vars), settings(warn_only=True):
        if env.verbose:
            run_cmd('phpunit --verbose')
        else:
            run_cmd('phpunit')


@task
def install_phpunit():
    """
    Install phpunit on target environment
    """
    require('settings', provided_by=['dev', 'staging', 'production'])
    run_cmd('wget https://phar.phpunit.de/phpunit.phar')
    run_cmd('chmod +x phpunit.phar')
    sudo('mv phpunit.phar /usr/local/bin/phpunit')


def scaffold_tests(dir=None):
    with cd(dir), settings(warn_only=True), shell_env(WP_TESTS_DIR=WP_TESTS_DIR, WP_CORE_DIR=WP_CORE_DIR):
        with hide('running'):
            tests_dir = run_cmd('ls tests')
            if tests_dir.find('No such file or directory') > -1:
                print(colors.cyan("Copying essential test files..."))

                sudo('mkdir tests')
                print(colors.cyan("Created 'tests' directory..."))

                # Install some basic sample test files
                print(colors.green("Copying test-sample.php and bootstrap.php"))
                put('tools/fablib/etc/test-sample.php', 'tests/test-sample.php', use_sudo=True)
                put('tools/fablib/etc/bootstrap-sample.php', 'tests/bootstrap.php', use_sudo=True)
            else:
                print(colors.yellow(
                    "Skip copying essential test files ('tests' directory already exists)..."))

            config_file = run_cmd('ls phpunit.xml')
            if config_file.find('No such file or directory') > -1:
                print(colors.green("Copying base phpunit.xml..."))
                put('tools/fablib/etc/phpunit-sample.xml', 'phpunit.xml', use_sudo=True)
            else:
                print(colors.yellow("Skip copying phpunit.xml (file already exists)..."))

            # Install the WP test framework
            sudo('rm -Rf %s' % WP_TESTS_DIR)
            print(colors.green("Installing the WordPress testing framework..."))
            vagrant.destroy_db(WP_TEST_DB)
            put('tools/fablib/etc/install-wp-tests.sh', '/tmp/install-wp-tests.sh', use_sudo=True)
            sudo('bash /tmp/install-wp-tests.sh %s root root localhost "%s"' % (WP_TEST_DB, WP_VERSION))


def get_path(theme_or_plugin=None, name=None):
    """
    Get the path for a theme or plugin
    """
    return helpers.capture("wp " + theme_or_plugin + " path " + name + " --dir", cmd_type='run')
