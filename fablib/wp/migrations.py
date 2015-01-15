import os
import re
import datetime

from fabric import colors
from fabric.api import get, task, settings
from fabric.contrib.console import confirm
from fabric.operations import prompt
from fabric.state import env

from getpass import getpass as _getpass

from .. import local as local_commands

NETWORK_TABLES = [
    'wp_users',
    'wp_usermeta',
]

BLOG_TABLES = [
    'wp_%s_commentmeta',
    'wp_%s_comments',
    'wp_%s_links',
    'wp_%s_options',
    'wp_%s_postmeta',
    'wp_%s_posts',
    'wp_%s_term_relationships',
    'wp_%s_term_taxonomy',
    'wp_%s_terms'
]

try:
    from local_fabfile import EXTRA_BLOG_TABLES
    BLOG_TABLES = BLOG_TABLES + EXTRA_BLOG_TABLES
except ImportError:
    pass

SQL_CLEANUP_SINGLE_BLOG = """
ALTER TABLE wp_users ADD spam tinyint(2) default 0;
ALTER TABLE wp_users ADD deleted tinyint(2) default 0;
UPDATE wp_usermeta SET meta_key = 'wp_%(new_blog_id)s_user_level' WHERE meta_key = 'wp_user_level';
UPDATE wp_usermeta SET meta_key = 'wp_%(new_blog_id)s_capabilities' WHERE meta_key = 'wp_capabilities';
UPDATE wp_posts SET post_content = replace(post_content, 'wp-content/uploads/', 'wp-content/blogs.dir/%(new_blog_id)s/files/');"""

@task(alias='s2m')
def single_to_multisite(name=None, new_blog_id=None, ftp_host=None, ftp_user=None, ftp_pass=None):
    """
    Migrate a stand alone blog to an existing multisite instance
    """
    try:
        import MySQLdb
        from MySQLdb import ProgrammingError as _ProgrammingError
    except ImportError:
        print(colors.yellow("""
    WARNING: Could not import MySQLdb module. If you plan on using any database migration commands, please install MySQLdb:

        pip install MySQLdb
    """))
        raise

    print("This script will help migrate a single WordPress blog to an existing\n"
        "WordPress multisite install by providing a SQL dump that you can\n"
        "apply to your Multisite database.")

    if name:
        env.single_blog_name = name
    else:
        raise Exception('A blog name is required')

    # Handle fetching and loading the single blog db in localhost mysql
    if ftp_host and ftp_user and ftp_pass:
        env.single_blog_host = ftp_host
        env.single_blog_user = ftp_user
        env.single_blog_pass = ftp_pass

        env.hosts = [env.single_blog_host, ]
        env.host_string = env.single_blog_host
        env.user = env.single_blog_user
        env.password = env.single_blog_pass

        print(colors.cyan("\nDownloading recent database backup for blog: %(single_blog_name)s\n" % env))
        get('wp-content/mysql.sql', 'mysql.sql')

    print(colors.cyan("(Re-)Loading database backup on localhost..."))
    with settings(warn_only=True):
        local_commands.destroy_db(env.single_blog_name)
        local_commands.create_db(env.single_blog_name)
        local_commands.load_db('mysql.sql', env.single_blog_name)

    db = MySQLdb.connect(
            host="localhost",
            user=env.local_db_user,
            passwd=env.local_db_pass,
            db=env.single_blog_name
        )
    db.autocommit(True)

    if new_blog_id:
        env.new_blog_id = new_blog_id
    else:
        raise Exception('The ID of a newly-created multisite blog is required')

    print(colors.cyan("\nWe'll rename all of the single blog's tables to use "
        "the appropriate blog ID prefix based on the ID: wp_%s_\n" % env.new_blog_id))

    SQL = SQL_CLEANUP_SINGLE_BLOG % env
    SQL = SQL + _generate_rename_tables_sql(db)

    # Run `SQL` against the single blog's db
    print(colors.cyan('Executing migration prep...'))
    for sql in SQL.split(";"):
        if sql.strip() != '':
            print(colors.green(sql))
            db.query(sql)

    # Dump the single blog's tables to a multisite_migration.sql file to apply to your multisite db
    _dump_tables(db)

    print(colors.green("\nUse multisite_migration.sql to migrate your multisite database!\n"))

    print("Cleaning up...\n")
    try:
        db.close()
    except _ProgrammingError:
        pass


def _dump_tables(db):
    print(colors.cyan("\nCreating migration file to apply to multisite database...\n"))

    with open('multisite_migration.sql', 'w+') as f:
        # Create temporary tables to help avoid inserting duplicates in wp_users and wp_usermeta tables.
        # Make sure we set the correct offset for user IDs
        # Preserve the site_url and home values in the options table
        content = """
DROP TEMPORARY TABLE IF EXISTS existing_users;
CREATE TEMPORARY TABLE IF NOT EXISTS existing_users SELECT ID, user_login FROM wp_users;

DROP TEMPORARY TABLE IF EXISTS existing_usermeta;
CREATE TEMPORARY TABLE IF NOT EXISTS existing_usermeta SELECT meta_value, umeta_id, user_id FROM wp_usermeta WHERE meta_key = 'nickname';

DROP FUNCTION IF EXISTS existingUser;
DELIMITER //
CREATE FUNCTION existingUser(ul VARCHAR(60))
RETURNS BIGINT
DETERMINISTIC
BEGIN
  DECLARE ret BIGINT;
  SET ret = (SELECT ID FROM existing_users WHERE user_login = ul LIMIT 1);
  RETURN ret;
END//
DELIMITER ;

DROP FUNCTION IF EXISTS existingUserMeta;
DELIMITER //
CREATE FUNCTION existingUserMeta(n VARCHAR(60))
RETURNS BIGINT
DETERMINISTIC
BEGIN
  DECLARE ret BIGINT;
  SET ret = (SELECT user_id FROM existing_usermeta WHERE meta_value = n LIMIT 1);
  RETURN ret;
END//
DELIMITER ;

SET @newUmetaID = (SELECT max(umeta_id) FROM wp_usermeta);
SET @newUserID = (SELECT max(ID) FROM wp_users);
SET @siteUrl = (SELECT option_value FROM wp_%(new_blog_id)s_options WHERE option_name = 'siteurl');
SET @homeVal = (SELECT option_value FROM wp_%(new_blog_id)s_options WHERE option_name = 'home');
    """ % env

        content = content + _get_blog_tables_sql(db)
        content = content + _get_network_tables_sql(db)

        # Also restore values in the options table
        content = content + """
UPDATE wp_%(new_blog_id)s_options SET option_value = @siteUrl WHERE option_name = 'siteurl';
UPDATE wp_%(new_blog_id)s_options SET option_value = @homeVal WHERE option_name = 'home';
UPDATE wp_%(new_blog_id)s_options SET option_value = "wp-content/blogs.dir/%(new_blog_id)s/files" WHERE option_name = 'upload_path';
""" % env

        # Finally, rename option 'wp_user_roles' to 'wp_%(new_blog_id)s_user_roles'
        content = content + """
UPDATE wp_%(new_blog_id)s_options SET option_name = 'wp_%(new_blog_id)s_user_roles' WHERE option_name = 'wp_user_roles';
""" % env

        # Drop the temporary tables and stored functions
        content = content + """
DROP TEMPORARY TABLE IF EXISTS existing_users;
DROP TEMPORARY TABLE IF EXISTS existing_usermeta;

DROP FUNCTION IF EXISTS existingUser;
DROP FUNCTION IF EXISTS existingUserMeta;
"""
        f.write(content)


def _generate_rename_tables_sql(db):
    print(colors.cyan("Getting list of tables to be renamed...\n"))
    query = """
    select TABLE_NAME from information_schema.tables where TABLE_SCHEMA = '%(single_blog_name)s'
    """ % env
    db.query(query)
    result = db.store_result()
    tables = [value['TABLE_NAME'] for value in result.fetch_row(result.num_rows(), 1)]

    # We don't want to rename wp_users or wp_usermeta
    for exclude in NETWORK_TABLES:
        tables.pop(tables.index(exclude))

    result = ''
    for tablename in tables:
        new_tablename = tablename.replace('wp_', 'wp_%s_' % env.new_blog_id)
        result += "rename table %s to %s;\n" % (tablename, new_tablename)

    return result


def _get_blog_tables_sql(db):
    ret = ''
    for table in BLOG_TABLES:
        table = table % env.new_blog_id

        if table == 'wp_%s_posts' % env.new_blog_id:
            # Ignore revision post types
            query = "select * from %s where post_type not in ('revision');" % (table, )
        elif table == 'wp_%s_postmeta' % env.new_blog_id:
            # Ignore meta for post_type = 'revision'
            query = "select * from %s where post_id not in (select ID from wp_%s_posts where post_type = 'revision');" % (table, env.new_blog_id)
        elif table == 'wp_%s_comments' % env.new_blog_id:
            # Only migrate non-spam comments
            query = "select * from %s where comment_approved not in ('spam');" % (table, )
        elif table == ' wp_%s_commentmeta' % env.new_blog_id:
            # Ignore meta for comment_approved = 'spam'
            query = "select * from %s where comment_ID not in (select comment_ID from wp_%s_comments where comment_approved = 'spam');" % (table, env.new_blog_id)
        else:
            # Get everything for other tables
            query = "select * from %s;"  % (table, );

        db.query(query)
        result = db.store_result()
        for idx in xrange(0, result.num_rows()):
            row = result.fetch_row(1, 1)
            data = row[0]
            values = []
            for key, value in data.iteritems():
                if key == 'post_author':
                    values.append("%s=@newUserID + %s" % (key, value))
                elif key == 'user_id':
                    values.append("%s=@newUserID + %s" % (key, value))
                elif type(value) == str:
                    values.append("%s=%s" % (key, db.escape(value)))
                elif type(value) == datetime.datetime:
                    values.append("%s='%s'" % (key, value))
                elif value is None:
                    pass
                else:
                    values.append("%s=%s" % (key, value))

            values_str = ', '.join([value for value in values])
            ret = ret + "REPLACE INTO %s SET %s;\n" % (table, values_str)

    return ret


def _get_network_tables_sql(db):
    ret = ''
    for table in NETWORK_TABLES:
        if table == 'wp_users':
            ret = ret + _wp_users_table_sql(db)
        if table == 'wp_usermeta':
            ret = ret + _wp_usermeta_table_sql(db)
    return ret


def _wp_users_table_sql(db):
    ret = "START TRANSACTION;\n"
    query = "select * from wp_users order by ID;"
    db.query(query)
    result = db.store_result()

    table_desc = result.describe()
    column_names = [column[0] for column in table_desc]
    column_names_str = ', '.join(column_names)

    rng = xrange(0, result.num_rows())
    for idx in rng:
        row = result.fetch_row(1, 1)
        data = row[0]
        values = []
        values_update = []

        for key in column_names:
            try:
                value = data[key]
            except KeyError:
                value = None

            if key == 'ID':
                old_user_id = value
                new_user_id = "@newUserID + %s" % (old_user_id,)
                values.append(new_user_id)
            elif type(value) == str:
                values.append("%s" % (db.escape(value), ))
                values_update.append("%s=%s" % (key, db.escape(value)))
            elif type(value) == datetime.datetime:
                values.append("'%s'" % (value, ))
                values_update.append("%s='%s'" % (key, value))
            elif value is None:
                values.append("NULL")
            else:
                values.append("%s" % (value, ))
                values_update.append("%s=%s" % (key, value))

        values_str = ', '.join(values)
        user_login = data['user_login']

        # If the user data hasn't been inserted, insert it.
        existing_user = "existingUser(%s)" % (db.escape(user_login), )
        ret = ret + "INSERT INTO wp_users (%s) SELECT %s FROM DUAL WHERE (SELECT %s) IS NULL;\n" % (
            column_names_str, values_str, existing_user)

        # If the user data exists, we want to update existing data
        values_str = ', '.join([value for value in values_update])
        ret = ret + "UPDATE wp_users SET %s WHERE ID = %s;\n" % (values_str, existing_user)

        # Change the post_author value from "@newUserID + [old_id]" to whatever
        # the existing user ID is determined to be.
        ret = ret + "UPDATE wp_%s_posts SET post_author = %s WHERE (SELECT %s) IS NOT NULL AND post_author = %s;\n" % (
            env.new_blog_id, existing_user, existing_user, new_user_id)

        # Do the same as above but for comments
        ret = ret + "UPDATE wp_%s_comments SET user_id = %s WHERE (SELECT %s) IS NOT NULL AND user_id = %s;\n" % (
            env.new_blog_id, existing_user, existing_user, new_user_id)

        if (idx % 1000) == 999:
            if idx != (len(rng) - 1):
                ret = ret + "COMMIT;\nSTART TRANSACTION;\n"

    ret = ret + "COMMIT;"

    return ret


def _wp_usermeta_table_sql(db):
    ret = "START TRANSACTION;\n"
    query = "select * from wp_usermeta order by user_id;"
    db.query(query)
    result = db.store_result()

    table_desc = result.describe()
    column_names = [column[0] for column in table_desc]
    column_names_str = ', '.join(column_names)

    rng = xrange(0, result.num_rows())
    for idx in rng:
        row = result.fetch_row(1, 1)
        data = row[0]
        values = []
        values_update = []

        for key in column_names:
            try:
                value = data[key]
            except KeyError:
                value = None

            if key == 'umeta_id': # usermeta table
                old_umeta_id = value
                new_umeta_id = "@newUmetaID + %s" % (old_umeta_id,)
                values.append(new_umeta_id)
            elif key == 'user_id':
                values.append("@newUserID + %s" % (value,))
            elif type(value) == str:
                values.append("%s" % (db.escape(value), ))
                values_update.append("%s=%s" % (key, db.escape(value)))
            elif type(value) == datetime.datetime:
                values.append("'%s'" % (value, ))
                values_update.append("%s='%s'" % (key, value))
            elif value is None:
                values.append("NULL")
            else:
                values.append("%s" % (value, ))
                values_update.append("%s=%s" % (key, value))

        values_str = ', '.join(values)

        nickname_query = "SELECT meta_value FROM wp_usermeta WHERE user_id = %s AND meta_key = 'nickname' LIMIT 1" % data['user_id']
        db.query(nickname_query)
        nickname_result = db.store_result()
        nickname_row = nickname_result.fetch_row(1, 1)

        try:
            user_nickname = db.escape(nickname_row[0]['meta_value'])
        except IndexError:
            continue

        existing_usermeta_query = "existingUserMeta(%s)" % (user_nickname, )

        # Again, if the data doesn't exist, insert it.
        ret = ret + "INSERT INTO wp_usermeta (%s) SELECT %s FROM DUAL WHERE (SELECT %s) IS NULL;\n" % (
            column_names_str, values_str, existing_usermeta_query)

        # If the user data exists, we want to update/replace existing data
        values_str = ', '.join([value for value in values_update])
        meta_key = data['meta_key']

        ret = ret + "UPDATE wp_usermeta SET %s WHERE user_id = (%s) AND meta_key = '%s';\n" % (
            values_str, existing_usermeta_query, meta_key)

        if (idx % 1000) == 999:
            if idx != (len(rng) - 1):
                ret = ret + "COMMIT;\nSTART TRANSACTION;\n"

    ret = ret + "COMMIT;"

    return ret
