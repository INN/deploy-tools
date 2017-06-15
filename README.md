# INN Deployment Tools

A box of tools for deploying INN's WordPress sites to WPEngine. Based on Chicago Tribune's [deploy-tools](https://github.com/newsapps/deploy-tools).

[Read documentation for all included commands here.](https://github.com/INN/deploy-tools/blob/master/COMMANDS.md)

## Prerequisites

You'll need Python (versions 2.5 to 2.7) and [pip](https://pip.pypa.io/en/latest/installing.html) to get started with these tools. [Virtualenv](https://virtualenv.pypa.io/en/latest/virtualenv.html) and [virtualenvwrapper](https://pypi.python.org/pypi/virtualenvwrapper/3.4) are not required, but using them is a good practice, so we'll use them here.

Set up python dev environment:

    $ sudo easy_install pip
    $ sudo pip install virtualenv
    $ sudo pip install virtualenvwrapper
    $ echo 'source /usr/local/bin/virtualenvwrapper.sh' >> ~/.zshrc

Change "~/.zshrc" to the appropriate rc file for your shell. If you're using bash: "~/.bashrc".

Open a new terminal window or tab and create a virtual environment for your project:

    $ mkvirtualenv projectnamegoeshere --no-site-packages
    $ workon projectnamegoeshere

## Setup

If you're creating an INN-style umbrella repository for a Wordpress site or multisite, these tools are already included in [the umbrella boilerplate](https://github.com/INN/umbrella-boilerplate/blob/master/docs/README.md).

If you're doing something else, read [the setup docs](docs/using-in-your-project.md).

## Usage

These tools use [Fabric](http://www.fabfile.org/).

To see a list of available commands:

    $ fab -l

Commands are documented in [COMMANDS.md](COMMANDS.md)

### Deployment

See [docs/deploy.md](docs/deploy.md)

A very long walk-through: https://gist.github.com/benlk/b75600e7243ac69f6e4275b65ba62d91

### Local development

If you want your own VM for development work, check out [docs/vagrant.md](docs/vagrant.md).

You can also use [Varying Vagrant Vagrants](https://github.com/Varying-Vagrant-Vagrants/VVV) with [vv](https://github.com/bradp/vv); INN umbrella repositories based off of [INN/umbrella-boilerplate](https://github.com/INN/umbrella-boilerplate) use that combination.

You can use Laravel Valet as well; the only difference is that you'll need to replace `vagrant` or `dev` commands with `local` ones. See [the list of commands](COMMANDS.md).

### Database commands

These tools include a few commands to ease database setup and manipulation. [Read about them here](https://github.com/INN/deploy-tools/blob/master/COMMANDS.md).

### Installing and/or upgrading WordPress

In setting up your dev environment, you'll want to pull in all the necessary WordPress files if they are not included in the project repository. To do this, use the command:

    $ fab wp.install:"4.8.1"

Where "4.8.1" identifies the [tagged version of the WordPress repository](https://github.com/WordPress/WordPress/tags) that you want to use.

Fabric will download the release .zip file from Github and extract its contents to the project root.

The `gitignore` file included in the examples directory is a good starter for WordPress projects destined for deployment to WPEngine. It will help keep your project repo tidy by ignoring all WordPress core files that are unnecessary for deployment. Simply rename it to `.gitignore` to use it. 
