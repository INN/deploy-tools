import os
import json
from pprint import pprint
from fabric.api import *
from fabric import colors

from StringIO import StringIO


def setup_tests(plugin):
  """
  Setup unit tests for a plugin
  """
  print(colors.cyan("Setting up tests for " + plugin + "..."));

  # Does this plugin exist?
  with cd(env.path):
      var = run('wp plugin list --format=json --fields=name', quiet=True)
      plugins = json.loads(var)
      if {'name': plugin} in plugins:
          print "Found plugin " + plugin
          print "Initalizing tests..."
          sudo("wp --allow-root scaffold plugin-tests " + plugin)
          directory = run("wp plugin path " + plugin + " --dir")
          with cd(directory):
              run('bash bin/install-wp-tests.sh largotest root root localhost latest')
      else:
          print("Warning: Could not find plugin: " + colors.red(plugin));


def run_tests(plugin):
  """
  Run unit tests for a plugin
  """
  with cd(env.path):
    directory = run("wp plugin path " + plugin + " --dir")
  with cd(directory):
    run('phpunit')


def pretty(d, indent=0):
   for key, value in d.iteritems():
      print '\t' * indent + str(key)
      if isinstance(value, dict):
         pretty(value, indent+1)
      else:
         print '\t' * (indent+1) + str(value)
