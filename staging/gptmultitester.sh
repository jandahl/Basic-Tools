#!/bin/bash

# Define the array with cURL protocols and options
curl_protocols=( "http:// -m 5 -I -L -k" "https:// -m 5 -I -L -k" )

# Define the multidimensional array with port numbers and usages
ports=("22,ssh","80,http" "443,https","3389,rdp","5900,vnc")

# Check if a command line argument is provided
if [[ $# -eq 0 ]]; then
    echo "Please provide a target host or IPv4 address as a command line argument."
    exit 1
fi

# Get the target hostname or IPv4 address from the command line argument
target=$1

# Output the target and do a DNS A lookup/reverse PTR lookup
echo "Target: $target ($(dig +short -x $target || dig +short $target)))"

# Try to reach the given target using cURL via http and then https
echo "Trying to reach $target via http and https using cURL..."
for protocol in "${curl_protocols[@]}"; do
    curl_command="curl ${protocol%% *}${target} ${protocol#* }"
    $curl_command >/dev/null 2>&1 && echo "${protocol%% *} : Success" || echo "${protocol%% *} : Failed"
done

# Try to reach each member of its multidimensional array via netcat
echo "Trying to reach $target via netcat..."
for port in "${ports[@]}"; do
    port_number="${port%,*}"
    port_usage="${port#*,}"
    nc -z -w5 $target $port_number >/dev/null 2>&1 && echo "$port_number ($port_usage): Success" || echo "$port_number ($port_usage): Failed"
done
