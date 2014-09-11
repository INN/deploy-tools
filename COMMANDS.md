# Included commands

These commands are all `fab` commands, and are run by entering `fab command:option,anotheroption,yetanotheroption`. For more information on Fabric, [see the official docs](http://docs.fabfile.org/en/1.9/tutorial.html).

## Enviornments and Branches

#### branch:name

**name** -- *Required.* The name of the branch to execute future commands with.

#### master

Work on development branch. Alias for `branch:master`

#### stable

Work on stable branch. Alias for `branch:production`

#### production

Work on defined production enviornment.

#### staging 

Work on defined staging enviornment.

## Database commands

### For MySQL on Vagrant

#### vagrant\_create\_db:name

**name** -- The database to create. If none is specified, the value of `env.project_name` is used.

#### vagrant\_destroy\_db:name

**name** -- The database to destroy. If none is specified, the value of `env.project_name` is used.

#### vagrant\_dump\_db:dump,name

**dump** -- The filename to dump the database to. If none is specified, defaults to `vagrant_dump.sql`.

**name** -- The name of the database to dump. If none is specified, the value of `env.project_name` will be used.

#### vagrant\_load\_db:dump,name

**dump** -- *Required.* The path of the dump to load.

**name** -- The name the database to load the dump file into. If none is specified, the deploy tools will use the value of `env.project_name`.

#### vagrant\_reload\_db:dump,name

**dump** -- *Required.* The path of the dump to load.

**name** -- The name the database to reload the dump file into. If none is specified, the deploy tools will use the value of `env.project_name`.

### For MySQL at localhost

#### local\_create\_db:name

**name** -- The database to create. If none is specified, the value of `env.project_name` is used.

#### local\_destroy\_db:name

**name** -- The database to destroy. If none is specified, the value of `env.project_name` is used.

#### local\_dump\_db:dump,name

**dump** -- The filename to dump the database to. If none is specified, defaults to `local_dump.sql`.

**name** -- The name of the database to dump. If none is specified, the value of `env.project_name` is used.

#### local\_load\_db:dump,name

**dump** -- *Required.* The path of the dump to load.

**name** -- The name the database to load the dump file into. If none is specified, the value of `env.project_name` is used.

#### local\_reload\_db:dump,name

**dump** -- *Required.* The path of the dump to load.

**name** -- The name the database to reload the dump file into. If none is specified, the deploy tools will use the value of `env.project_name`.


## Deploying

#### dry_run

Don't transfer files, just output what would happen during a real deployment.

#### path:path

**path** -- *Required.* The project's path on the remote server.

#### deploy

Deploy local copy of repository to target WP Engine environment.

#### rollback

Deploy the most recent rollback point.


## General utilities

#### fetch\_sql\_dump

Fetches a recent database dump from WPEngine and saves it as `mysql.sql` in the root of your project directory.

#### search\_replace:file,search,replacement

This function is meant to help clean up a database dump so that it can be used for local development on the Vagrant box.

However, it can serve as a general search and replace function for any text file.

**file** -- *Required.* The path to the file to perform the search and replace operation on.

**search** -- *Required.* A string to search for in the file. For example: "largoproject.org"

**replacement** -- A string to replace your search term with. For example: "someotherdomain.com". If none is specified, defaults to "vagrant.dev."

#### single_to_multisite_migration

#### install_wordpress

**version** -- *Required.* Downloads specified version of WordPress from https://github.com/WordPress/WordPress and installs it.

#### single_to_multisite_migration

Migrate a stand alone blog to an existing multisite instance

#### verify_prerequisites

Checks to make sure you have curl (with ssh) and git-ftp installed, Attempts installation via brew if you do not.
