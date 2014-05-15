# INN Deployment Tools

A box of tools for deploying INN's WordPress sites to WPEngine. Based on Chicago Tribune's [deploy-tools](https://github.com/newsapps/deploy-tools).

## Prerequisites

You'll need Python and pip to get started with these tools. Virtualenv and virtualenvwrapper are not required, but using them is a good practice.

Setup python dev environment

    $ sudo easy_install pip
    $ sudo pip install virtualenv
    $ sudo pip install virtualenvwrapper
    $ echo 'source /usr/local/bin/virtualenvwrapper.sh' >> ~/.zshrc

Change "~/.zshrc" to the appropriate rc file for your shell. If you're using bash: "~/.bashrc".

Open a new terminal window or tab and create a virtual environment for your project:

    $ mkvirtualenv projectnamegoeshere --no-site-packages
    $ workon projectnamegoeshere

## Setup

To use these tools, add this repo as a git submodule in the root of your project:

	$ git submodule add https://github.com/INN/deploy-tools.git tools

Then pull the example files in to the root of your project:

	$ cp -Rf tools/examples/* ./

Install the required libraries with pip:

Note: if you're using OS X Mavericks (10.9), you might need to set some compiler flags for Fabric and its dependencies to install correctly:

    $ export CFLAGS=-Qunused-arguments
    $ export CPPFLAGS=-Qunused-arguments

Then:

    $ workon projectnamegoeshere
    $ pip install -r requirements.txt
    $ fab verify_prerequisites

Now edit the `fabfile.py` and adjust the settings for your project.

## Usage

### Deployment

These tools use [Fabric](http://www.fabfile.org/).

To see a list of available commands:

    $ fab -l

To deploy to your staging environment:

    $ fab staging master deploy

And production:

    $ fab production master deploy

To switch to a different branch and deploy

    $ fab staging branch:newfeaturebranchname deploy

### Local development with Vagrant

The examples directory also includes a `Vagrantfile`, a bunch of config files for Apache, PHP, MySQL and a `boot-script.sh` for provisioning a Vagrant instance for local development.

Assuming you have VirtualBox and Vagrant installed, start the Vagrant box with:

    $ vagrant up

It should take about ten minutes to complete the provisioning process.

When the Vagrant box is ready, you'll want to edit your `/etc/hosts` file (i.e. not the `hosts` file on the Vagrant box), adding:

    192.168.33.10 vagrant.dev

Once you've done that, you should be able to visit [http://vagrant.dev](http://vagrant.dev) and see your project running.

A couple notes:

- The Apache configuration for our Vagrant box uses the root directory of your project as the www root for vagrant.dev.
- Our provisioning script installs mysql and sets a password for the root user with value 'root'.

### Installing and/or upgrading WordPress

In setting up your dev environment, you'll want to pull in all the necessary WordPress files if they are not included in the project repository. To do this, use the command:

    $ fab upgrade_wordpress:"3.9.1"

Where "3.9.1" identifies the tagged version of the [WordPress repository](https://github.com/WordPress/WordPress) that you want to use.

Fabric will download the release .zip file from Github and extract its contents to the project root.

The `gitignore` file included in the examples directory is a good starter for WordPress projects destined for deployment to WPEngine. It will help keep your project repo tidy by ignoring all WordPress core files that are unnecessary for deployment.
