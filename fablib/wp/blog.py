import os

from fabric.api import require, task
from fabric import colors

from cmd import cmd

__all__ = ['dump_settings', 'load_settings', ]


@task
def dump_settings(blog_id=None):
    """
    Dumps a blog's options, sidebars/widgets and menu configurations to JSON files in your
    project's data directory.
    """
    print(colors.cyan("Dumping settings for blog ID: %s to the `data` directory" % blog_id))

    if not blog_id:
        raise ValueError("blog_id must not be None")

    require('settings', provided_by=["production", "staging", "dev", ])

    if not os.path.exists('data'):
        os.makedirs('data')

    print(colors.green("Dumping menu configuration..."))
    cmd('menus_dump', blog_id=blog_id, output='data/blog-%s-menus.json' % blog_id)

    print(colors.green("Dumping sidebar configuration..."))
    cmd('sidebars_dump', blog_id=blog_id, output='data/blog-%s-sidebars.json' % blog_id)

    print(colors.green("Dumping options configuration..."))
    cmd('options_dump', blog_id=blog_id, output='data/blog-%s-options.json' % blog_id)


@task
def load_settings(blog_id=None):
    """
    Load a blog's option, sidebars/widgets and menu configurations via the
    data/blog-{blog_id}-{type}.json files created with the dump_settings command.
    """
    print(colors.cyan("Loading settings for blog ID: %s from the `data` directory" % blog_id))

    print(colors.red(
        "\nWARNING: always search and replace the source domain name on the target" +
        " environment after loading settings\n"))

    if not blog_id:
        raise ValueError("blog_id must not be None")

    require('settings', provided_by=["production", "staging", "dev", ])

    print(colors.green("Loading menu configuration..."))
    cmd('menus_load', blog_id=blog_id, json_data='data/blog-%s-menus.json' % blog_id)

    print(colors.green("Loading sidebar configuration..."))
    cmd('sidebars_load', blog_id=blog_id, json_data='data/blog-%s-sidebars.json' % blog_id)

    print(colors.green("Loading options configuration..."))
    cmd('options_load', blog_id=blog_id, json_data='data/blog-%s-options.json' % blog_id)
