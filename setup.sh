#! /bin/bash
MODULE_DIR=$1
REDIS_PORT=$2

# install the basics
sudo apt-get update
sudo apt-get install -y python-dev python-pip
sudo pip install virtualenv

# setup redis
cd ~
wget http://download.redis.io/redis-stable.tar.gz
tar -xvzf redis-stable.tar.gz
rm redis-stable.tar.gz

cd redis-stable
make
sudo cp src/redis-server /usr/local/bin
sudo cp src/redis-cli /usr/local/bin
sudo mkdir /etc/redis
sudo mkdir -p /var/redis/$REDIS_PORT
sudo cp utils/redis_init_script /etc/init.d/redis_$REDIS_PORT

# make virtualenv
virtualenv .venv
source .venv/bin/activate

# pip install
cd $MODULE_DIR/core/MPy
pip install -r requirements.txt

deactivate .venv

# symlink all media
cd $MODULE_DIR/core/media
ln -s $MODULE_DIR/media/* .