import io
import os
import re
import subprocess
import sys
import time

from functools import partial
from multiprocessing.dummy import Pool
from multiprocessing import Process

from fabric import colors
from fabric.api import cd, local, task
from fabric.state import env

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
    compile(directory, wait=True)

@task
def compile(directory='.', wait=False):
    pool = Pool()
    tasks = {}

    for root, dirs, files in os.walk(directory):
        skip = bool([pattern for pattern in IGNORE if root.find(pattern) > 0])
        if skip:
            continue

        paths = []
        if 'Gruntfile.js' in files and 'package.json' in files and 'node_modules' in dirs:
            paths.append(root)

        for path in paths:
            tasks.update({ path: pool.apply(_compile, args=([path, wait])) })

    try:
        pool.close()
        pool.join()
        os.wait()

        # Spit out anything that was sent to STDOUT while our grunt commands ran
        sep = '----------'
        for path, task in tasks.iteritems():
            print sep, colors.cyan('Log for path: %s' % path), sep
            print task.stdout.read()
    except KeyboardInterrupt:
        print(colors.red('Keyboard Interrupt. Exiting...'))
        pool.terminate()


def _compile(path, wait):
    if wait:
        print(colors.cyan('Watching files in: %s' % path))
        return subprocess.Popen(['grunt watch'], shell=True, cwd=path)
    else:
        print(colors.cyan('Compiling files in: %s' % path))
        return subprocess.Popen(['grunt less'], shell=True, cwd=path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
