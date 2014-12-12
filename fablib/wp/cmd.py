import json
import os
import pickle
import requests

from fabric.api import task, require
from fabric.state import env
from fabric.operations import prompt
from getpass import getpass
from pyquery import PyQuery as pq

session = requests.session()

WP_SCRIPTS_DIR = 'wp-scripts'
HEADERS = { 'User-Agent': 'Anything goes here' }

__all__ = ['cmd', ]


@task(default=True)
def cmd(cmd_slug, json_data=None, output=None, **kwargs):
    """
    Run a command on the specified environment over HTTP
    """
    require('settings', provided_by=["production", "staging", "dev", ])

    url = 'http://%s/%s/%s.php' % (env.domain, WP_SCRIPTS_DIR, cmd_slug)

    if kwargs:
        query_string = '&'.join(["%s=%s" % (key, value) for key, value in kwargs.iteritems()])
        url = url + "?" + query_string

    if json_data:
        # Make sure we have valid json before proceeding
        try:
            data = json.loads(json_data)
        except ValueError:
            try:
                f = open(os.path.expanduser(json_data))
                json_data = f.read()
                json.loads(json_data)
                f.close()
            except IOError:
                print "Could not parse JSON data."

        ret = post(url, data={ 'json': json_data })
    else:
        ret = get(url)

    if ret.status_code is 200:
        try:
            if output:
                with open(os.path.expanduser(output), 'w+') as f:
                    f.write(json.dumps(json.loads(ret.content), sort_keys=True))
            else:
                print json.dumps(json.loads(ret.content), sort_keys=True)
        except ValueError:
            if output:
                with open(os.path.expanduser(output), 'w+') as f:
                    f.write(ret.content)
            else:
                print ret.content
    else:
        print "Command request returned: %s %s" % (ret.status_code, ret.reason)


# Utilities
def save_cookies(requests_cookiejar, filename):
    """
    Save cookies to file.
    """
    with open(filename, 'wb') as f:
        pickle.dump(requests_cookiejar, f)


def load_cookies(filename):
    """
    Load cookies from file.
    """
    with open(filename, 'rb') as f:
        return pickle.load(f)


def authenticate(username=None, password=None):
    """
    POST username and password as if logging in via the browser.
    """
    if not username:
        username = prompt("Username: ")
    if not password:
        password = getpass("Password: ")

    wp_login = requests.get('http://%s/wp-login.php' % env.domain, headers=HEADERS)

    markup = pq(wp_login.content)
    form = markup.find('form')
    action = form.attr('action')

    form_data = {
        'log': username,
        'pwd': password,
        'submit': 'Log in',
        'testcookie': '1'
    }
    return requests.post(action, data=form_data, headers=HEADERS)


def post(url, data=None, json=None, **kwargs):
    """
    Authenticated POST request.
    """
    if not authenticated():
        ret = authenticate()
        save_cookies(ret.cookies, os.path.expanduser(cookies_file()))
        kwargs['cookies'] = ret.cookies
    else:
        kwargs['cookies'] = load_cookies(os.path.expanduser(cookies_file()))

    kwargs['headers'] = HEADERS

    return requests.post(url, data=data, json=json, **kwargs)


def get(url, **kwargs):
    """
    Authenticated GET request.
    """
    if not authenticated():
        ret = authenticate()
        kwargs['cookies'] = ret.cookies
        save_cookies(ret.cookies, os.path.expanduser(cookies_file()))
    else:
        kwargs['cookies'] = load_cookies(os.path.expanduser(cookies_file()))

    kwargs['headers'] = HEADERS

    return requests.get(url, **kwargs)


def authenticated():
    """
    Try to reach the WordPress dashboard. If we're redirected to the login page, we must not be authenticated.
    """
    try:
        ret = requests.get(
            'http://%s/wp-admin/' % env.domain,
            cookies=load_cookies(os.path.expanduser(cookies_file())),
            allow_redirects=False,
            headers=HEADERS
        )
        if ret.status_code in [301, 302]:
            return False
        elif ret.status_code is 200:
            return True
    except IOError:
        return False


def cookies_file():
    return '/tmp/cookies_%s.txt' % env.domain
