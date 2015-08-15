## MetroPictures

A fake IVR for Raspberry Pi, built for Camille Henrot's interactive sculptures.

### Features:

*	Registers input from circuits with RPi.GPIO package
*	Manages the flow of our fake IVR
*	Allows for easy updates (audio and video files) from our custom FTP server
*	Saves states with Redis as necessary
*	Provides an HTML-based testing console for trying out interactions without touching any wiring

### Implementation

Each sculpture requires this core library in its root directory.  Other than that, two components are needed:

1.	Python module
1.	config file

Please have a look at any of the "sculpture packages" for an example of how to use the core library.

### Config Files

Config files should be called `config.json` and be placed in the root directory.  Here's an example config file:

```
{
	"rpi_id" : "echo_priest",
	"api_port" : 8080,
	"num_processes" : 3,
	"redis_port" : 6379,
	"receiver_pin" : 2,
	"media_manifest" : [
		"video",
		"confessions",
		"absolutions"
	],
	"cdn" : {
		"addr" : "127.0.0.1",
		"port" : 8082,
		"user" : "anonymous",
		"home_dir" : "EchoPriest"
	}
}

```

The `rpi_id` directive is a short code for the Raspberry Pi running the sculpture.  Alphanumeric, no spaces or special characters.

The `api_port` directive corresponds to the ports python is listening on.  The `redis_port` directive should be self-explainatory.

The `receiver_pin` directive is the GPIO pin that registers someone picking up or hanging up the "phone".  (Other pins are mapped in the corresponding python module.)

The `media_manifest` directive is an array referring to the folders that will hold media.  All of these folders will be created on setup, regardless of whether they contain media.  During setup, any files destined for those folders will be pulled down from the FTP server.

The `cdn_directive` is an object that describes how to connect to the FTP server.  The `home_dir` directive here is the root folder containing the sculpture's files.  So far, only anonymous connections are supported.

### CDN

An [FTP server](https://github.com/MetroPictures/MPCDN) exists to push the necessary files to the sculptures (which are, of course, too large to be hosted here).  Conventionally, each sculpture should have a `prompts` folder (full of mp3s for the IVR to "say").  If the sculpture includes video, a `video` folder is required.

### Testing Console

Hey guess what?  There's also an HTML-based testing console for trying interactions without having to rig up any buttons on the Raspberry Pi.  Start up the engine, and open a browser to localhost:8080 (or whatever port the api is set to).  You will see a keypad (modeled after a telephone, naturally) that you can use.

### Setup

After cloning, run `git submodule update --init --recursive`.  Then create your config file.  From the root directory run `python core/setup.py`.

### Usage

*	Run: `python [module_name].py --start`
*	Stop: `python [module_name].py --stop`
*	Restart `python [module_name].py --restart`
