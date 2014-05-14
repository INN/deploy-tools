#!/bin/bash

USERNAME=vagrant

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
    libgdal1-dev vim curl python-software-properties

# install everything but the kitchen sink
echo "Installing LAMP stack"
install_pkg apache2 mysql-server libapache2-mod-auth-mysql \
    php5-mysql php5 libapache2-mod-php5 php5-mcrypt

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

# Restart everything
service apache2 restart
service mysql restart

# Mysql cleanup message
echo ""
echo "To finish installing mysql, login to your vagrant box:"
echo "    $ vagrant ssh"
echo "And run:"
echo "    $ mysql_install_db"
echo "    $ mysql_secure_installation"
echo ""

# Edit your local /etc/hosts file if you want
echo ""
echo "Add the following to your /etc/hosts file:"
echo "192.168.33.10 vagrant.dev"
echo "Visit `vagrant.dev` to see your project up and running"
echo ""

echo 'All setup!'
