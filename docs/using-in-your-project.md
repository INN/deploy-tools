# Setup

If you're creating an INN-style umbrella repository for a Wordpress site or multisite, these tools are already included in [the umbrella boilerplate](https://github.com/INN/umbrella-boilerplate/blob/master/docs/README.md).

If you're doing something else, read on.

To use these tools in your project, add this repo as a git submodule in the root of your project, in the `tools` directory:

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
    $ fab wp.verify_prerequisites

The `wp.verify_prerequisites` command will notify you of any issues that might prevent you from using the deploy tools in their entirety.

Now edit the example `fabfile.py` to adjust the settings for your project:

    env.project_name = ''   # name for the project

You'll also want to supply the ssh environment variables for `production` and `staging` (or any other enviornments).

    env.hosts       = []    # ssh host for production.
    env.user        = ''    # ssh user for production.
    env.password    = ''    # ssh password for production.

    env.hosts       = []    # ssh host for staging.
    env.user        = ''    # ssh user for staging.
    env.password    = ''    # ssh password for staging.

By default, the deploy tools will use git for deployment to WP Engine. If you'd rather use sftp to deploy, you can do so by specifying `sftp_deploy` in your `fabfile.py`.

    env.sftp_deploy = True

After setting `env.sftp_deploy` to `True`, make sure you run `wp.verify_prerequisites` to ensure you have the required software installed.

If your version of curl does not support sftp and you wish to use the tools in this repository to deploy, you will have to use a version of curl that does support it. For OSX users, the verification script uses brew to take care of that problem. For users of other operating systems, check your online support communities. Ubuntu users may have success in following [this guide](http://zeroset.mnim.org/2013/03/14/sftp-support-for-curl-in-ubuntu-12-10-quantal-quetzal-and-later/).


