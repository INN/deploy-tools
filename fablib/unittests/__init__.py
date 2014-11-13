import os
import json
from pprint import pprint
from fabric.api import *
from fabric import colors
from ..helpers import _capture
from ..vagrant import vagrant_destroy_db

from StringIO import StringIO

WP_TEST_DB = 'largotest'
WP_TESTS_DIR = '/tmp/wordpress-tests-lib'


def setup_tests(name):
    """
    Setup unit tests for a theme or plugin
    """
    require('settings', provided_by=['vagrant', ])

    print(colors.cyan("Setting up tests for " + name + "..."))

    # Does this theme or plugin exist?
    with cd(env.path):
        plugins = json.loads(_capture('wp plugin list --format=json --fields=name', type='run'))
        themes = json.loads(_capture('wp theme list --format=json --fields=name', type='run'))

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


def run_tests(name):
    """
    Run unit tests for a theme or plugin
    """
    require('settings', provided_by=['vagrant', ])

    with cd(env.path):
        plugins = json.loads(_capture('wp plugin list --format=json --fields=name', type='run'))
        themes = json.loads(_capture('wp theme list --format=json --fields=name', type='run'))

        test = { 'name': name }
        if test in plugins:
            directory = get_path('plugin', name)
        elif test in themes:
            directory = get_path('theme', name)

    with cd(directory), shell_env(WP_TESTS_DIR=WP_TESTS_DIR):
        run('phpunit')


def scaffold_tests(dir=None):
    with cd(dir), settings(warn_only=True), shell_env(WP_TESTS_DIR=WP_TESTS_DIR):
        with hide('running', 'stderr', 'stdout', 'warnings', 'debug'):
            tests_dir = run('ls tests')
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

            config_file = run('ls phpunit.xml')
            if config_file.find('No such file or directory') > -1:
                print(colors.green("Copying base phpunit.xml..."))
                put('tools/fablib/etc/phpunit-sample.xml', 'phpunit.xml', use_sudo=True)
            else:
                print(colors.yellow("Skip copying phpunit.xml (file already exists)..."))

            # Install the WP test framework
            framework_dir = run('ls %s' % WP_TESTS_DIR)
            if framework_dir.find('No such file or directory') > -1:
                print(colors.green("Installing the WordPress testing framework..."))
                vagrant_destroy_db(WP_TEST_DB)
                put('tools/fablib/etc/install-wp-tests.sh', '/tmp/install-wp-tests.sh', use_sudo=True)
                run('bash /tmp/install-wp-tests.sh %s root root localhost latest' % WP_TEST_DB)
            else:
                print(colors.yellow("Skip install of WordPress testing framework (already installed)..."))


def get_path(type=None, name=None):
    """
    Get the path for a theme or plugin
    """
    return _capture("wp " + type + " path " + name + " --dir", type='run')


def install_phpunit():
    require('settings', provided_by=['vagrant', ])
    run('wget https://phar.phpunit.de/phpunit.phar')
    run('chmod +x phpunit.phar')
    sudo('mv phpunit.phar /usr/local/bin/phpunit')
