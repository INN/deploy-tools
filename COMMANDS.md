# Included commands

These are all `fab` commands and are run this way:

    $ fab command:option,anotheroption,yetanotheroption

For more information about Fabric, [see the official docs](http://docs.fabfile.org/en/1.9/tutorial.html).

## Table of contents

- [Environment and branch commands](#environment-and-branch-commands)
- [Database commands](#database-commands)
- [Deploying](#deploying)
- [WordPress utilities](#wordpress-utilities)
- [General utilities](#general-utilities)

## Environment and branch commands

### Environments

#### production

Work on production enviornment.

#### staging

Work on staging enviornment.

#### dev

Work on the development (vagrant) environment

### Branches

#### branch:name

**name** -- *Required.* The name of the branch to switch to before running subsequent commands.

#### master

Work on development branch. Alias for `branch:master`

#### stable

Work on stable branch. Alias for `branch:production`


## Database commands

### For MySQL on Vagrant

#### vagrant.create\_db:name

**name** -- The database to create. If none is specified, the value of `env.project_name` is used.

#### vagrant.destroy\_db:name

**name** -- The database to destroy. If none is specified, the value of `env.project_name` is used.

#### vagrant.dump\_db:dump,name

**dump** -- The filename to dump the database to. If none is specified, defaults to `vagrant_dump.sql`.

**name** -- The name of the database to dump. If none is specified, the value of `env.project_name` will be used.

#### vagrant.load\_db:dump,name

**dump** -- *Required.* The path of the dump to load.

**name** -- The name the database to load the dump file into. If none is specified, the deploy tools will use the value of `env.project_name`.

#### vagrant.reload\_db:dump,name

**dump** -- *Required.* The path of the dump to load.

**name** -- The name the database to reload the dump file into. If none is specified, the deploy tools will use the value of `env.project_name`.

### For MySQL at localhost

#### local.create\_db:name

**name** -- The database to create. If none is specified, the value of `env.project_name` is used.

#### local.destroy\_db:name

**name** -- The database to destroy. If none is specified, the value of `env.project_name` is used.

#### local.dump\_db:dump,name

**dump** -- The filename to dump the database to. If none is specified, defaults to `local_dump.sql`.

**name** -- The name of the database to dump. If none is specified, the value of `env.project_name` is used.

#### local.load\_db:dump,name

**dump** -- *Required.* The path of the dump to load.

**name** -- The name the database to load the dump file into. If none is specified, the value of `env.project_name` is used.

#### local.reload\_db:dump,name

**dump** -- *Required.* The path of the dump to load.

**name** -- The name the database to reload the dump file into. If none is specified, the deploy tools will use the value of `env.project_name`.


## Deploying

#### dry_run

Don't transfer files, just output what would happen during a real deployment.

#### verbose

Show more information about what's happening as code is deployed.

#### deploy

Deploy local copy of repository to target WP Engine environment.

#### rollback

Deploy the most recent rollback point.


## WordPress utilities

### General WordPress utilities

#### wp.fetch\_sql\_dump

Fetches a recent database dump from WPEngine and saves it as `mysql.sql` in the root of your project directory.

#### wp.install:version

Downloads specified version of WordPress from https://github.com/WordPress/WordPress and installs it.

**version** -- *Required.* A version number to install (e.g. "3.9.1").

#### wp.single_to_multisite_migration

Migrate a stand alone blog to an existing multisite instance

#### wp.verify_prerequisites

Checks to make sure you have curl (with ssh) and git-ftp installed, Attempts installation via brew if you do not.

### Maintenance mode commands

#### wp.maintenance.start

Prevents users from logging into the WordPress dashboard by modifying your project's `.htaccess` file on the specified environment.

#### wp.maintenance.stop

Removes the barrier put in place by `wp.maintenance.start`.

### Unit test scaffolding and test runner for plugins and themes

#### wp.tests.setup:theme_or_plugin

Generates files need to run PHPUnit tests for a plugin or theme included in your project.

**theme_or_plugin** -- *Required* The directory name of the plugin or theme to generate test files for.

#### wp.tests.run:theme_or_plugin

Runs PHPUnit tests for the specified theme or plugin. Displays results of the tests.

**theme_or_plugin** -- *Required* The directory name of the plugin or theme to run tests for.

## General utilities

#### rollback

Deploy the most recent rollback point.

#### helpers.search\_replace:file,search,replacement

This function is meant to help clean up a database dump so that it can be used for local development on the Vagrant box.

However, it can serve as a general search and replace function for any text file.

**file** -- *Required.* The path to the file to perform the search and replace operation on.

**search** -- *Required.* A string to search for in the file. For example: "largoproject.org"

**replacement** -- A string to replace your search term with. For example: "someotherdomain.com". If none is specified, defaults to "vagrant.dev."
