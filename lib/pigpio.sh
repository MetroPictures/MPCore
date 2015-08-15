#! /bin/bash

touch /var/lock/pigpio

case "$1" in
	start)
		echo "starting pigpio"
		sudo pigpiod
		;;
	stop)
		echo "stopping pigpio"
		sudo kill -9 $(pgrep "pigpiod")
		;;
	*)
		echo "usage: /etc/init.d/pigpio {start|stop}"
		exit 1
		;;
esac
exit 0