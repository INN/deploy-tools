import time
import os
import subprocess

from multiprocessing import Pool

from fabric import colors
from fabric.api import local, task

IGNORE = ['.git', '.svn', 'node_modules']


@task
def bootstrap(directory='.'):
    """
    Recrusively search for Gruntfile.js and package.json, run `npm install` in directories where
    those files are present.
    """
    for root, dirs, files in os.walk(directory):
        skip = bool([pattern for pattern in IGNORE if root.find(pattern) > 0])
        if skip:
            continue

        if 'Gruntfile.js' in files and 'package.json' in files and 'node_modules' not in dirs:
            local('cd %s && npm install' % root)
            continue


@task
def watch(directory='.'):
    """
    Search for a Gruntfile.js and run the `grunt watch` command in the directory where the Gruntfile
    is present.
    """
    compile(directory, watch=True)


@task(default=True)
def compile(directory='.', watch=False):
    """
    Search for a Gruntfile.js and run the `grunt less` command in the directory where the Gruntfile
    is present.
    """
    tasks = []

    for root, dirs, files in os.walk(directory):
        skip = bool([pattern for pattern in IGNORE if root.find(pattern) > 0])
        if skip:
            continue

        paths = []
        if 'Gruntfile.js' in files and 'package.json' in files and 'node_modules' in dirs:
            paths.append(root)

        for path in paths:
            tasks.append((path, watch))

    """
    TODO: Find a more elegant way of settings the max processes for `pool`.

    Since we're essentially using a Pool to check the status of our Grunt commands, this shouldn't
    cause any major performance issues, but it would be nice to use a Queue, especially when we're
    not watching for changes, but simply compiling.
    """
    pool = Pool(len(tasks))
    if watch:
        pool.map_async(_compile, tasks)
    else:
        pool.map_async(_compile, tasks, callback=_get_output)
    pool.close()
    pool.join()

    if watch:
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pool.terminate()
            print colors.red("Exiting...")


def _get_output(results):
    sep = '----------'
    for path, messages, result in results:
        print sep, colors.cyan("Log for path: %s" % path), sep
        for message in messages:
            print message


def _compile(args):
    path, watch = args
    messages = []
    if watch:
        print(colors.cyan('Watching files in: %s' % path))
        result = subprocess.Popen(['grunt', 'watch'], cwd=path)
    else:
        print(colors.cyan('Compiling files in: %s' % path))
        result = subprocess.Popen(['grunt', 'less'], cwd=path, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        result.wait()
        if result.stdout:
            messages.append(result.stdout.read())
        if result.stderr:
            messages.appen(result.stderr.read())
    return path, messages, result
