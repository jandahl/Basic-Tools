### Note for Windows users
It might, it might'nt work. There's a little leeway for Cygwin somewhere in the code but don't expect it to work out of the box. Pull Requests are welcome!

## Basic Tools
 Basic Tools that should make your life easier. 

 Usually there's a help/usage screen if you run them without parameters.

### `multitester`
 Tool that `ping`s, `curl`s and `netcat`s the target domain or IPv4 IP. No consideration made for IPv6, currently.  
 It also verifies A og PTR records on the way through.  
 
 Tries to guess the relevant `ping` flags based on your system, but not sure how extremely weird systems will affect it, e.g. `Cygwin` but with `GNU ping`.  
 
 Example: `multitester.sh google.com`
 
![CleanShot 2021-03-24 at 12 38 13](https://user-images.githubusercontent.com/657507/112304692-129e0780-8c9e-11eb-8c50-8f15c77219d2.png)

### `ottomator`
 Script that uses [`clogin`](https://www.systutorials.com/docs/linux/man/1-clogin/) from [Shrubbery Networks' `rancid`](https://www.shrubbery.net/rancid/) to throw a bunch of commands to a bunch of devices based on filenames. Very simple. 

### `up`
 `up-yours` is a simple script that assumes that the last command line argument is a target host/ip that is down.  
 It continually pings the host until it gets a reply, after which it runs the entire command after its invocation, e.g. `up ssh -l root 10.20.30.40`. 

### `flaplogger`
 Takes a host/ip that it then logs to screen when it tries to ping and whether it succeeded or not. Not updated since 2016 and not tested either. YMMV.

### `pingu`
 Pings a host and gives you a status at a set interval. Logs to a file. Interval defaults to 5 seconds.
