import paramiko

from fabric.api import *
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


def start_maintenance():
    """
    Prevents users from logging into the WordPress dashboard
    """
    htaccess = _get_htaccess()
    lines = htaccess.readlines()
    updated_lines = []
    for line in lines:
        updated_lines.append(line)
        if line.strip() == 'RewriteBase /':
            updated_lines.append(MAINTENANCE_REWRITE)
    _write_maintenance_html()
    _write_htaccess(updated_lines)


def stop_maintenance():
    """
    Removes barrier to users attempting to login to the WordPress dashboard
    """
    htaccess = _get_htaccess()
    lines = htaccess.readlines()
    updated_lines = []
    for line in lines:
        if line != MAINTENANCE_REWRITE:
            updated_lines.append(line)
    _remove_maintenance_html()
    _write_htaccess(updated_lines)


def _get_htaccess():
    if not env.path:
        env.path = ''
    htaccess = StringIO()
    get(remote_path='%s/.htaccess' % env.path, local_path=htaccess)
    htaccess.seek(0)
    return htaccess


def _write_htaccess(lines):
    if not env.path:
        env.path = ''
    htaccess = StringIO()
    htaccess.writelines(lines)
    htaccess.seek(0)
    put(remote_path='%s/.htaccess' % env.path, local_path=htaccess, use_sudo=_use_sudo())


def _write_maintenance_html():
    html = StringIO()
    html.write(MAINTENANCE_HTML)
    put(remote_path='%s/maintenance.html' % env.path, local_path=html, use_sudo=_use_sudo())


def _remove_maintenance_html():
    if env.settings == 'vagrant':
        with cd(env.path):
            sudo('rm maintenance.html')
    else:
        _sftp_remove('%s/maintenance.html' % env.path)


def _use_sudo():
    if env.settings == 'vagrant':
        return True
    else:
        return False


def _sftp_remove(path):
    transport = paramiko.Transport((env.hosts[0], int(env.port)))
    transport.connect(username=env.user, password=env.password)
    sftp = paramiko.SFTPClient.from_transport(transport)
    sftp.remove(path)
