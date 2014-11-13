import paramiko

from fabric.api import task, get, put
from fabric.state import env
from fabric import colors

from StringIO import StringIO

MAINTENANCE_REWRITE = "RewriteRule ^wp-admin(.+) maintenance.html [R=302,L]\n"
MAINTENANCE_HTML = """
<!DOCTYPE html>
<html>
    <head>
        <title>Down For Maintenance</title>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <style>
        h1 { font-size: 50px; }
        body { text-align:center; font: 20px Helvetica, sans-serif; color: #333; }
        </style>
    </head>
    <body>
        <h1>Down For Maintenance</h1>
	<p>Sorry for the inconvenience, but we're performing site maintenance at the moment.</p>
	<p>We'll be back online shortly!</p>
    </body>
</html>"""


@task
def start():
    """
    Prevents users from logging into the WordPress dashboard
    """
    htaccess = get_htaccess()
    lines = htaccess.readlines()
    updated_lines = []
    for line in lines:
        updated_lines.append(line)
        if line.strip() == 'RewriteBase /':
            updated_lines.append(MAINTENANCE_REWRITE)
    write_maintenance_html()
    write_htaccess(updated_lines)


@task
def stop():
    """
    Removes barrier to users attempting to login to the WordPress dashboard
    """
    htaccess = get_htaccess()
    lines = htaccess.readlines()
    updated_lines = []
    for line in lines:
        if line != MAINTENANCE_REWRITE:
            updated_lines.append(line)
    remove_maintenance_html()
    write_htaccess(updated_lines)


def get_htaccess():
    if not env.path:
        env.path = ''
    htaccess = StringIO()
    get(remote_path='%s/.htaccess' % env.path, local_path=htaccess)
    htaccess.seek(0)
    return htaccess


def write_htaccess(lines):
    if not env.path:
        env.path = ''
    htaccess = StringIO()
    htaccess.writelines(lines)
    htaccess.seek(0)
    put(remote_path='%s/.htaccess' % env.path, local_path=htaccess, use_sudo=use_sudo())


def write_maintenance_html():
    html = StringIO()
    html.write(MAINTENANCE_HTML)
    put(remote_path='%s/maintenance.html' % env.path, local_path=html, use_sudo=use_sudo())


def remove_maintenance_html():
    if env.settings == 'vagrant':
        with cd(env.path):
            sudo('rm maintenance.html')
    else:
        sftp_remove('%s/maintenance.html' % env.path)


def use_sudo():
    if env.settings == 'vagrant':
        return True
    else:
        return False


def sftp_remove(path):
    transport = paramiko.Transport((env.hosts[0], int(env.port)))
    transport.connect(username=env.user, password=env.password)
    sftp = paramiko.SFTPClient.from_transport(transport)
    sftp.remove(path)
