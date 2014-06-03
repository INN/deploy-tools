import os
import re

from fabric.api import *
from fabric import colors

from fabric.contrib.console import confirm
from fabric.operations import prompt

from getpass import getpass

from ..local import *

MULTISITE_TABLES = ['wp_users', 'wp_usermeta', ]
BLOG_TABLES = [
    'wp_%s_commentmeta', 'wp_%s_comments', 'wp_%s_links', 'wp_%s_options', 'wp_%s_postmeta',
    'wp_%s_posts', 'wp_%s_term_relationships', 'wp_%s_term_taxonomy', 'wp_%s_terms']

SQL_CLEANUP_SINGLE_BLOG = """
alter table wp_users add spam tinyint(2);
alter table wp_users add deleted tinyint(2);
set @newID = %(new_start_id)s;
update wp_users set ID = ID + @newID;
update wp_usermeta set user_id = user_id + @newID;
update wp_usermeta set meta_key = 'wp_%(new_blog_id)s_user_level' where meta_key = 'wp_user_level';
update wp_usermeta set meta_key = 'wp_%(new_blog_id)s_capabilities' where meta_key = 'wp_capabilities';
update wp_posts set post_author = post_author + @newID;
update wp_posts set post_content = replace(
post_content,
'wp-content/uploads/',
'wp-content/blogs.dir/%(new_blog_id)s/files/'
);
update wp_comments set user_id = user_id + @newID;"""


def single_to_multisite_migration():
    """
    Migrate a stand alone blog to an existing multisite instance
    """
    print("This script will help migrate a single WordPress blog to an existing\n"
        "WordPress multisite install by providing a SQL dump that you can\n"
        "apply to your Multisite database. You'll need FTP login info for the\n"
        "single blog. Let's get started...\n")

    # Handle fetching and loading the single blog db in localhost mysql
    print("1. Please provide...\n")
    env.single_blog_name = prompt("Name of single blog (e.g. 'myblog'): ")
    env.single_blog_host = prompt("FTP host of single blog: ")
    env.single_blog_user = prompt("FTP user name: ")
    env.single_blog_pass = getpass("FTP user password: ")

    env.hosts = [env.single_blog_host, ]
    env.host_string = env.single_blog_host
    env.user = env.single_blog_user
    env.password = env.single_blog_pass

    print(colors.cyan("\nDownloading recent database backup for blog: %(single_blog_name)s\n" % env))
    get('wp-content/mysql.sql', 'mysql.sql')

    print(colors.cyan("(Re-)Loading database backup on localhost..."))
    with settings(warn_only=True):
        local_destroy_db(env.single_blog_name)
        local_create_db(env.single_blog_name)
        local_load_db('mysql.sql', env.single_blog_name)

    print("\n2. We'll need to make sure our single blog's user ID's\n"
        "are migrated so that they are outside the range of existing\n"
        "ID's in the multisite database. Run the following SQL against\n"
        "your multisite database to find the maximum user ID: \n")

    print(colors.yellow("    select max(ID) from wp_users;\n"))

    result = prompt(
        "\nPlease enter the value of max(ID) returned by the SQL statement: ")

    env.new_start_id = int(result)

    print("\nExcellent. Based on your input, we'll migrate \n"
        "our single blog's user table, adjusting user ID's.\n")

    print(colors.cyan("The user ID renumbering will start at %s" % (env.new_start_id + 1)))

    print("\n3. Next, create a new blog in your multisite WordPress install \n"
        "for the single blog that we are migrating.\n")

    env.new_blog_id = prompt("\nLocate the newly created blog's ID and enter it here: ")

    print(colors.cyan("\nWe'll rename all of the single blog's tables to use "
        "the appropriate blog ID prefix based on the ID: wp_%s_\n" % env.new_blog_id))

    SQL = SQL_CLEANUP_SINGLE_BLOG % env

    print(colors.cyan("Getting list of tables to be renamed...\n"))
    result = local(
        'mysql -u %(local_db_user)s -p%(local_db_pass)s -N -B -e "select TABLE_NAME from information_schema.tables ' \
        'where TABLE_SCHEMA = \'%(single_blog_name)s\'" 2>/dev/null' % env, capture=True);

    tables = result.splitlines()

    # We don't want to rename wp_users or wp_usermeta
    for exclude in MULTISITE_TABLES:
        tables.pop(tables.index(exclude))

    for tablename in tables:
        new_tablename = tablename.replace('wp_', 'wp_%s_' % env.new_blog_id)
        SQL += 'rename table %s to %s;' % (tablename, new_tablename)

    print("\nWe're ready to run the migration against your local copy of the single blog's database.\n")

    if confirm("4. Proceed with the migration? "):
        print(colors.cyan("\nMigrating local copy of database...\n"))

        with open('migration.sql', 'w+') as f:
            f.write(SQL)

        result = local(
            'mysql -u %(local_db_user)s -p%(local_db_pass)s ' \
            '%(single_blog_name)s < migration.sql 2>/dev/null' % env)

        if confirm("\n5. Create migration files to apply to multisite database?"):
            print(colors.cyan("\nCreating migration file for network tables (wp_users, wp_usermeta)...\n"))
            env.network_tables_string = ' '.join(MULTISITE_TABLES)
            local('mysqldump -u %(local_db_user)s -p%(local_db_pass)s ' \
                '--skip-triggers --compact --no-create-info ' \
                '%(single_blog_name)s %(network_tables_string)s > ' \
                'network_tables_migration.sql 2>/dev/null' % env)

            print(colors.cyan("Creating migration file for the migrated blog...\n"))
            env.blog_tables_string = ' '.join([table % env.new_blog_id for table in BLOG_TABLES])
            local('mysqldump -u %(local_db_user)s -p%(local_db_pass)s ' \
                '%(single_blog_name)s %(blog_tables_string)s > ' \
                'blog_tables_migration.sql 2>/dev/null' % env)

            print(colors.green(
                "\nUse network_tables_migration.sql and blog_tables_migration.sql to migrate your multisite database!\n"))

        print("Cleaning up...\n")
        local('rm migration.sql mysql.sql')
    else:
        print(colors.cyan("\nOutput SQL statements to: migration.sql"))
        print("Cleaning up...\n")
        local('rm mysql.sql')
