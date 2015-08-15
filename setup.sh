#! /bin/bash
MODULE_DIR=$1
REDIS_PORT=$2

# install the basics
sudo apt-get update
sudo apt-get install -y python-dev python-pip lsof screen

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
sudo update-rc.d redis_$REDIS_PORT defaults

# pip install 
sudo pip install -r $MODULE_DIR/core/requirements.txt

# fix for sound card, don't you know?

# symlink all media
cd $MODULE_DIR/core/media
ln -s $MODULE_DIR/media/* .