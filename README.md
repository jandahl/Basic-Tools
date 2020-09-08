## Basic Tools
 Basic Tools that should make your life easier

 Usually there's a help/usage screen if you run them without parameters.

### `multitester.sh`
 Tool that `ping`s, `curl`s and `netcat`s the target domain or IPv4 IP. No consideration made for IPv6, currently.  
 It also verifies A og PTR records on the way through.
 Example: `multitester.sh google.com`

### `ottomator.sh`
 Script that uses [`clogin`](https://www.systutorials.com/docs/linux/man/1-clogin/) from [Shrubbery Networks' `rancid`](https://www.shrubbery.net/rancid/) to throw a bunch of commands to a bunch of devices based on filenames. Very simple. 

### `up`
 `up-yours` is a simple script that assumes that the last command line argument is a target host/ip that is down.  
 It continually pings the host until it gets a reply, after which it runs the entire command after its invocation, e.g. `up ssh -l root 10.20.30.40`. 

### flaplogger
 Takes a host/ip that it then logs to screen when it tries to ping and whether it succeeded or not. Not updated since 2016 and not tested either. YMMV.