# Assumptions:

- A WordPress multisite database loaded on your Vagrant box, accessible at `vagrant.dev` with the IP address 192.168.33.10 (See your `Vagrantfile` and `/etc/hosts`)
- WordPress already installed and configured on your Vagrant box
- [WP-CLI](http://wp-cli.org/) installed on your Vagrant box
- The main site of your network is `network.org` and the project site is `project.org`
- If you do not possess admin credentials for the network, we will create a new admin, whose username is `admin` and whose password is `password`.
- If you want to be able to undo this, run `vagrant plugin install vagrant-vbox-snapshot` from the Vagrant host. To take a snapshot, run `vagrant snapshot take default [optional-name-for-snapshot]`. Take one before starting, and then at the start of every major section here.

# Getting multisite set up:

## Correcting the network site name:

Grab Version 2.x of https://interconnectit.com/products/search-and-replace-for-wordpress-databases/ and unzip it into the root of your Vagrant site. That's either into `/vagrant` or into the folder containing the wordpress install. Either way, it should be in the same folder as `wp-config.php`.

Visit http://vagrant.dev/searchreplacedb2.php in your browser.

1. Check "Pre-populate the DB values"
2. Click "Submit"
3. Check that the values look right. If you're using our Vagrantfile from deploy-tools, it will be localhost, largoproject, root, root, utf8.
4. There is a multi-select of database tables. Most will be prefixed with `wp_#_`, as opposed to `wp_`. Ctrl-click or shift-click to choose the non-number-prefixed tables. 
5. Check 'Leave GUID column unchaged'
6. Search for `network.org` and replace with `vagrant.dev`
7. Submit search string.

Open `wp-config.php` and add the follwing lines: 

	define('MULTISITE', true);
	define('SUBDOMAIN_INSTALL', true);
	define('DOMAIN_CURRENT_SITE', 'vagrant.dev');
	define('PATH_CURRENT_SITE', '/');
	define('SITE_ID_CURRENT_SITE', 1);
	define('BLOG_ID_CURRENT_SITE', 1);

## Adding a new super-user

This is only necessary if you do not possess the credentials for a network super-admin. 

	vagrant ssh
	cd /vagrant
	wp user create admin admin@vagrant.dev --role=administrator --user_pass=password
	wp super-admin add admin

You should now be able to log into http://vagrant.dev/wp-login.php as `admin` with `password`. 

# Getting access to the sites on your multisite

## Add your user to `project.org`

You only need to do this if your admin user does not have access to `project.org`.

Log into your multisite install at http://vagrant.dev/wp-login.php.

1. In the header, choose My Sites > Network Admin > Sites (http://vagrant.dev/wp-admin/network/sites.php)
2. Find the `project.org` site. Click on its "Edit" button. 
3. Find the site's URL near the top of the page: "Edit Site: project.org" or "Edit Site: project.vagrant.dev"
4. Edit your host computer's `/etc/hosts` file by adding the line `192.168.33.10 project.vagrant.dev` to the end of the file.
5. Check that http://project.vagrant.dev points to the correct site.
6. Click the "Users" tab.
7. Under "Add Existing User", enter `admin` as the username and choose the "Administrator" role.

## Find the blog ID of `project.org`

1. Go to http://vagrant.dev/wp-admin/network/sites.php
2. Find the `project.org` site. Click on its "Edit" button. 
3. Find the site's URL near the top of the page: "Edit Site: project.org" or "Edit Site: project.vagrant.dev"
4. Find the ID number in the browser's current URL: http://vagrant.dev/wp-admin/network/site-info.php?id=53
7. Copy down the blog ID number. We'll use it in the next step.

## Convert `project.org` to `project.vagrant.dev`

This process will be familiar, with one key difference.

Visit http://vagrant.dev/searchreplacedb2.php in your browser.

1. Check "Pre-populate the DB values"
2. Click "Submit"
3. Check that the values look right. If you're using our Vagrantfile from deploy-tools, it will be localhost, largoproject, root, root, utf8.
4. There is a multi-select of database tables. Ctrl-click or shift-click to **choose the tables prefixed with wp_53_**, where 53 is the site id.
5. Check 'Leave GUID column unchaged'
6. Search for `project.org` and replace with `project.vagrant.dev`
7. Submit search string.
8. Wait. The page will load for a loooong time.
9. If you get to a page with a success message, congratulations!  
    "In the process of replacing "project.org" with "project.vagrant.dev" we scanned 33 tables with a total of 610470 rows, 71588 cells were changed and 71560 db update performed and it all took 958.267747 seconds."
10. If the next page is mostly or entirely blank after the header, then you will need to use a different tool to perform the replace.

You should now be able to log in as `admin` with `password` at http://project.vagrant.dev/wp-login.php