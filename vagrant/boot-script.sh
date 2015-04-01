#!/bin/bash

USERNAME=vagrant

VAGRANT_DB_USER=root
VAGRANT_DB_PASS=root

# Some useful bash functions

# install_pkgs $pkg_name
function install_pkg {
    echo "Installing packages $*"
    DEBIAN_FRONTEND='noninteractive' \
    apt-get -q -y -o Dpkg::Options::='--force-confnew' install \
            $*
}

# Make sure we have a locale defined
echo 'Setting locale ...'
export LANGUAGE=en_US.UTF-8
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
locale-gen en_US.UTF-8
dpkg-reconfigure locales

# Set the timezone
echo "US/Central" > /etc/timezone
dpkg-reconfigure --frontend noninteractive tzdata

# update the software
echo "Updating OS..."
export DEBIAN_FRONTEND=noninteractive
apt-get -q update && apt-get -q upgrade -y

# grab some basic utilities
echo "Installing common libraries"
install_pkg build-essential python-setuptools python-dev zip \
    git-core unattended-upgrades mailutils libevent-dev \
    mdadm xfsprogs s3cmd python-pip python-virtualenv python-all-dev \
    virtualenvwrapper libxml2-dev libxslt-dev libgeos-dev \
    libpq-dev postgresql-client mysql-client libmysqlclient-dev \
    runit proj libfreetype6-dev libjpeg-dev zlib1g-dev \
    libgdal1-dev vim curl python-software-properties memcached \
    php-pear subversion

# install everything but the kitchen sink
echo "Installing LAMP stack"

# Set mysql root password
debconf-set-selections <<< "mysql-server mysql-server/root_password password $VAGRANT_DB_PASS"
debconf-set-selections <<< "mysql-server mysql-server/root_password_again password $VAGRANT_DB_PASS"

install_pkg apache2 mysql-server libapache2-mod-auth-mysql \
    php5-mysql php5 libapache2-mod-php5 php5-mcrypt php5-memcache \
    php5-gd

# Install memcached php extension
yes '' | pecl install memcached
echo "extension=memcache.so" | tee /etc/php5/conf.d/memcache.ini

# Make PIL build correctly
ln -s /usr/lib/x86_64-linux-gnu/libfreetype.so /usr/lib/
ln -s /usr/lib/x86_64-linux-gnu/libz.so /usr/lib/
ln -s /usr/lib/x86_64-linux-gnu/libjpeg.so /usr/lib/

echo "Setting up user environment..."

# Pull down assets
ASSET_DIR="/vagrant/tools/vagrant/assets"

cd /home/$USERNAME

# fix asset permissions
chown -Rf root:root $ASSET_DIR
chmod -Rf 755 $ASSET_DIR

# Install assets
echo "Applying overlay from tools/vagrant/assets/overlay"
rsync -r $ASSET_DIR/overlay/ /

# install scripts
echo "Installing scripts from tools/vagrant/assets/bin"
cp $ASSET_DIR/bin/* /usr/local/bin

# Copy ssh config
echo "Installing keys and ssh config from tools/vagrant/assets/ssh"
cp $ASSET_DIR/ssh/* /home/$USERNAME/.ssh/

# make sure our clocks are always on time
echo 'ntpdate ntp.ubuntu.com' > /etc/cron.daily/ntpdate
chmod +x /etc/cron.daily/ntpdate

# fix permissions in ssh folder
chmod -Rf go-rwx /home/$USERNAME/.ssh

# setup some directories
mkdir /home/$USERNAME/logs

# Fix any perms that might have gotten messed up
chown -Rf $USERNAME:$USERNAME /home/$USERNAME

# make sure our user is a member of the web group
usermod -a -G www-data $USERNAME

# Enable our dev site
a2ensite vagrant

# Make sure Apache's rewrite module is enabled
a2enmod rewrite

# Set mysql root user permissions
mysql -u $VAGRANT_DB_USER -p$VAGRANT_DB_PASS -e "grant all privileges on *.* to '$VAGRANT_DB_USER'@'%' identified by '$VAGRANT_DB_PASS'";

# Install WP CLI
curl -O https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar
chmod +x wp-cli.phar
mv wp-cli.phar /usr/local/bin/wp

# Install PHPUnit for wp unit testing.
wget https://phar.phpunit.de/phpunit.phar
chmod +x phpunit.phar
mv phpunit.phar /usr/local/bin/phpunit

# Set up PHP error log
touch /home/$USERNAME/logs/php_errors.log
chown $USERNAME:www-data /home/$USERNAME/logs/php_errors.log

# Restart everything
service apache2 restart
service mysql restart

# Edit your local /etc/hosts file if you want
echo ""
echo "Add the following to your /etc/hosts file:"
echo "192.168.33.10 vagrant.dev"
echo "Visit vagrant.dev to see your project up and running"
echo ""

echo 'All setup!'
