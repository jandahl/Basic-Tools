#!/bin/bash


### ChatGPT 3.5 prompt:
# I would like a bash script that has a prepulated multidimensional array with PORT NUMBER and PORT USAGE, e.g. "80","http";"443","https". The script should expect a target host or IPv4 address as a command line argument and give a help screen if it does not receive one. If it receives a valid command line argument, it should then proceed to: 1) Output the target on screen and do a DNS A lookup/reverse PTR lookup and print this in a parenthesis. 2) Try to reach the given target using curl (or similar), given a separate multidimensional array. 3) For each member of its multidimensional array it should try to reach it via raw sockets. The script should accept several hostnames and/or IPs. Also, I should like to be able to serve this script command line arguments that add port numbers to either curl (or similar) (e.g. "-c 25;smtp,8080" or "-c 25;smtp,8080") or raw sockets (e.g. "-p 25;smtp,8080" or "--ports 25;smtp,8080"), and an option for a retry timer in seconds (e.g. "-r 10" or "--retry 10"). Failure and success messages should be abstracted to variables that can be shared and should be in the form of emojis. Use try/catch to avoid crashes. If any of the commands hang for one second, it should count as a failure. 

#!/bin/bash

# Define the two multidimensional arrays
curl_ports=( ["80"]="http" ["443"]="https" )
raw_ports=( ["25"]="SMTP" ["110"]="POP3" )

# Parse command-line arguments
if [ $# -eq 0 ]; then
  echo "Usage: $0 <target>"
  exit 1
fi

# Perform a DNS lookup of the target
target=$1
ip=$(nslookup $target | awk '/^Address: / { print $2 }')

# Test the target with curl
for port in "${!curl_ports[@]}"; do
  protocol=${curl_ports[$port]}
  output=$(curl --connect-timeout 1 -sI "http://$target:$port" 2>&1)
  if echo "$output" | grep -q "HTTP/1.1"; then
    echo "$target ($ip) is running $protocol on port $port"
  else
    echo "$target ($ip) is not running $protocol on port $port"
  fi
done

# Test the target with raw sockets
for port in "${!raw_ports[@]}"; do
  protocol=${raw_ports[$port]}
  output=$( ( trap "" ALRM ; ( echo "" | nc -z $target $port >/dev/null 2>&1 ) & alarm 1 ) 2>&1 )
  if echo "$output" | grep -q "succeeded"; then
    echo "$target ($ip) is running $protocol on port $port"
  else
    echo "$target ($ip) is not running $protocol on port $port"
  fi
done
