import os
import re

from fabric.api import *
from fabric import colors

from fabric.contrib.console import confirm
from fabric.operations import prompt

from getpass import getpass

from ..local import *

NETWORK_TABLES = ['wp_users', 'wp_usermeta', ]
BLOG_TABLES = [
    'wp_%s_commentmeta', 'wp_%s_comments', 'wp_%s_links', 'wp_%s_options', 'wp_%s_postmeta',
    'wp_%s_posts', 'wp_%s_term_relationships', 'wp_%s_term_taxonomy', 'wp_%s_terms']

SQL_CLEANUP_SINGLE_BLOG = """
alter table wp_users add spam tinyint(2) default 0;
alter table wp_users add deleted tinyint(2) default 0;
update wp_usermeta set meta_key = 'wp_%(new_blog_id)s_user_level' where meta_key = 'wp_user_level';
update wp_usermeta set meta_key = 'wp_%(new_blog_id)s_capabilities' where meta_key = 'wp_capabilities';
update wp_posts set post_content = replace(
post_content,
'wp-content/uploads/',
'wp-content/blogs.dir/%(new_blog_id)s/files/'
);"""


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

    print("\n2. Next, create a new blog in your multisite WordPress install \n"
        "for the single blog that we are migrating.\n")

    env.new_blog_id = prompt("\nLocate the newly created blog's ID and enter it here: ")

    print(colors.cyan("\nWe'll rename all of the single blog's tables to use "
        "the appropriate blog ID prefix based on the ID: wp_%s_\n" % env.new_blog_id))

    SQL = SQL_CLEANUP_SINGLE_BLOG % env
    SQL = SQL + _generate_rename_tables_sql()

    print("\nWe're ready to run the migration against your local copy of the single blog's database.\n")

    if confirm("3. Proceed with the migration? "):
        print(colors.cyan("\nMigrating local copy of database...\n"))

        with open('migration.sql', 'w+') as f:
            f.write(SQL)

        result = local(
            'mysql -u %(local_db_user)s -p%(local_db_pass)s ' \
            '%(single_blog_name)s < migration.sql 2>/dev/null' % env)

        if confirm("\n5. Create migration files to apply to multisite database?"):
            _dump_tables()

            print(colors.green(
                "\nUse multisite_migration.sql to migrate your multisite database!\n"))

        print("Cleaning up...\n")
        local('rm migration.sql mysql.sql')
    else:
        print(colors.cyan("\nOutput SQL statements to: migration.sql"))
        print("Cleaning up...\n")
        local('rm mysql.sql')


def _dump_tables():
    print(colors.cyan("\nCreating migration file to apply to multisite database...\n"))
    blog_tables_string = ' '.join([table % env.new_blog_id for table in BLOG_TABLES])
    network_tables_string = ' '.join(NETWORK_TABLES)

    env.tables_string = blog_tables_string + ' ' + network_tables_string

    content = local('mysqldump -u %(local_db_user)s -p%(local_db_pass)s --skip-triggers --compact --replace ' \
        '--no-create-info --skip-opt --single-transaction %(single_blog_name)s %(tables_string)s' % env, capture=True)

    with open('multisite_migration.sql', 'w+') as f:
        # Set proper offsets for primary keys and user IDs throughout the dump
        content = re.sub(r'`wp_users`\sVALUES\s\(', '`wp_users` VALUES (@newUserID +', content)
        content = re.sub(r'`wp_usermeta`\sVALUES\s\((\d+),', r'`wp_usermeta` VALUES (\g<1>, @newUserID +', content)
        content = re.sub(r'`wp_usermeta`\sVALUES\s\(', '`wp_usermeta` VALUES (@newUmetaID +', content)

        # Prepend values for new primary keys and user IDs to the dump
        content = """set @newUmetaID = (select max(umeta_id) from wp_usermeta);
        set @newUserID = (select max(ID) from wp_users);""" + content

        # Also preserve the siteurl, home, upload_url_path of the blog you just created in the multisite database
        content = ("""set @siteUrl = (select option_value from wp_%(new_blog_id)s_options where option_name = 'siteurl');
        set @homeVal = (select option_value from wp_%(new_blog_id)s_options where option_name = 'home');
        set @uploadUrlPath = (select option_value from wp_%(new_blog_id)s_options where option_name = 'upload_url_path');""" % env) + content

        # Once we've imported all of the content, go back and make sure all of the user IDs
        # in comments and posts tables are set properly.
        content = content + """update wp_%(new_blog_id)s_posts set post_author = post_author + @newUserID;
        update wp_%(new_blog_id)s_comments set user_id = user_id + @newUserID;""" % env

        # Also restore values in the options table
        content = content + """update wp_%(new_blog_id)s_options set option_value = @siteUrl where option_name = 'siteurl';
        update wp_%(new_blog_id)s_options set option_value = @homeVal where option_name = 'home';
        update wp_%(new_blog_id)s_options set option_value = @uploadUrlPath where option_name = 'upload_url_path';""" % env

        # Finally, rename option 'wp_user_roles' to 'wp_%(new_blog_id)s_user_roles'
        content = content + """update wp_%(new_blog_id)s_options set option_name = 'wp_%(new_blog_id)s_user_roles' where option_name = 'wp_user_roles';""" % env

        f.write(content)


def _generate_rename_tables_sql():
    print(colors.cyan("Getting list of tables to be renamed...\n"))
    result = local(
        'mysql -u %(local_db_user)s -p%(local_db_pass)s -N -B -e "select TABLE_NAME from information_schema.tables ' \
        'where TABLE_SCHEMA = \'%(single_blog_name)s\'" 2>/dev/null' % env, capture=True);

    tables = result.splitlines()

    # We don't want to rename wp_users or wp_usermeta
    for exclude in NETWORK_TABLES:
        tables.pop(tables.index(exclude))

    result = ''
    for tablename in tables:
        new_tablename = tablename.replace('wp_', 'wp_%s_' % env.new_blog_id)
        result += "rename table %s to %s;\n" % (tablename, new_tablename)

    return result
