#	Install RPi with NOOBS

1.	Use **Disk Utility** to format a new SD card. Click root of disk, and select the Erase tab.  Format should be ExFat (MS-DOS) and give your pi a name. Click Erase. 
1.	Unzip the install files to your newly-formatted drive:
	`unzip /path/to/NOOBS.zip -d /path/to/new/drive`
1.	Unmount the new drive and pop it into the RPi.  Turn it on and install Raspbian.  When this finishes, click "OK" to boot up for the first time.
1.	**Change your root password to something you like.**
1.	In advanced options, **enable SSH.**
1.	In advanced options, **enable I2C**

At any point, if you need to change these configuations, run `sudo raspi-config`.

#	Update packages

1.	Modify `/etc/apt/sources.list` for the current repositories:
	```
	deb http://archive.raspbian.org/raspbian wheezy main contrib non-free rpi
	deb-src http://archive.raspbian.org/raspbian wheezy main contrib non-free rpi
	```
1.	Install Raspbian public key:
	`wget http://archive.raspbian.org/raspbian.public.key -O - | sudo apt-key add -`
1.	Update and upgrade:
	`sudo apt-get update && sudo apt-get upgrade`

#	Networking

1.	Give your RPi a Static IP address
1.	Set DNS nameservers
	`vi /etc/networking/interfaces`

#	Setup Git

1.	Add your private key to the pi.  Does not have to be at `~/.ssh/id_rsa`, but be sure to update your ssh config file if it's in an alternative directory.

#	Enable I2C

1.	Check `/etc/modprobe.d/raspi-blacklist.conf` to see if the i2c library is disabled.  It should not be-- in fact, this file should be empty.  However, if it's not, make the necessary change.

1.	Modify `/etc/modules`:
	```
	i2c-bcm2708
	i2c-dev
	```

1.	Modify `/boot/config.txt`:
	```
	dtparam=i2c1=on
	dtparam=i2c_arm=on
	```

#	Soundcards

1.	Set your USB soundcard as the default.  Edit `/etc/modprob.d/alsa-base.conf` and set the directive `options snd-usb-audio index=-2` to `options snd-usb-audio index=0`.
1.	Modify your `~/.asoundrc` file to explicitly set card 0 as default.
	```
	pcm.!default {
		type hw
		card 0
	}

	ctl.!default {
		type hw
		card 0
	}
	```

#	Finally, reboot

All these settings should update on reboot.