# Vagrant

This repository ships with a default configuration. You do not have to use it; any repository built off of INN's [boilerplate umbrella](https://github.com/INN/umbrella-boilerplate) uses [VVV](https://github.com/Varying-Vagrant-Vagrants/VVV) with [vv](https://github.com/bradp/vv) instead.

The examples directory includes a `Vagrantfile`, a bunch of config files for Apache, PHP, MySQL and a `boot-script.sh` for provisioning a Vagrant instance for local development.

Assuming you have [VirtualBox](https://www.virtualbox.org/wiki/Downloads) and [Vagrant](http://www.vagrantup.com/downloads.html) installed, and enough spare disk space, start the Vagrant box with:

    $ vagrant up

It should take about ten minutes to complete the provisioning process, depending on your internet connection speed. 

When the Vagrant box is ready, you'll want to edit your `/etc/hosts` file (i.e. not the `hosts` file on the Vagrant box), adding:

    192.168.33.10 vagrant.dev

Once you've done that, you should be able to visit [http://vagrant.dev](http://vagrant.dev) and see your project running.

A couple notes:

- The Apache configuration for our Vagrant box uses the root directory of your project as the www root for vagrant.dev.
- Our provisioning script installs mysql and sets a password for the root user with value 'root'.

