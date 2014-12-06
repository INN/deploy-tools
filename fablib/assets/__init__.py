import os
import subprocess

from multiprocessing import Pool

from fabric import colors
from fabric.api import local, task

IGNORE = ['.git', '.svn', 'node_modules']


@task
def bootstrap(directory='.'):
    for root, dirs, files in os.walk(directory):
        skip = bool([pattern for pattern in IGNORE if root.find(pattern) > 0])
        if skip:
            continue

        if 'Gruntfile.js' in files and 'package.json' in files and 'node_modules' not in dirs:
            local('cd %s && npm install' % root)
            continue


@task
def watch(directory='.'):
    compile(directory, watch=True)

@task
def compile(directory='.', watch=False):
    pool = Pool()
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

    pool.map_async(_compile, tasks)
    pool.close()
    pool.join()

    if watch:
        try:
            while True:
                pass
        except KeyboardInterrupt:
            pool.terminate()
            print colors.red("Exiting...")


def _compile(args):
    path, watch = args
    if watch:
        print(colors.cyan('Watching files in: %s' % path))
        result = subprocess.Popen(['grunt', 'watch'], cwd=path)
    else:
        sep = '----------'
        print(colors.cyan('Compiling files in: %s' % path))
        result = subprocess.Popen(['grunt', 'less'], cwd=path, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        result.wait()
        if result.stdout:
            print sep, colors.cyan("Log for path: %s" % path), sep
            print result.stdout.read()
        if result.stderr:
            print sep, colors.red("Errors for path: %s" % path), sep
            print result.stderr.read()
    return result
