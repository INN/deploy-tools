# INN Deployment Tools

A box of tools for deploying INN's WordPress sites to WPEngine. Based on Chicago Tribune's [deploy-tools](https://github.com/newsapps/deploy-tools).

## Prerequisites

You'll need Python and pip to get started with these tools. Virtualenv and virtualenvwrapper are not required, but using them is a good practice.

Setup python dev environment

    $ sudo easy_install pip
    $ sudo pip install virtualenv
    $ sudo pip install virtualenvwrapper
    $ echo 'source /usr/local/bin/virtualenvwrapper.sh' >> ~/.zshrc

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

Now edit the `fabfile.py` and adjust the settings for your project.

## Usage

These tools use [Fabric](http://www.fabfile.org/).

To see a list of available commands:

    $ fab -l

To deploy to your staging environment:

    $ fab staging master deploy

And production:

    $ fab production master deploy

To switch to a different branch and deploy

    $ fab staging branch:newfeaturebranchname deploy
