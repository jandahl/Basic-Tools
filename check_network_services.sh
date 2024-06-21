#!/bin/bash

# Constants for colors
GREEN="\033[32m"
RED="\033[31m"
RESET="\033[0m"
# Constants for indicators
allOK="${GREEN}✦${RESET}"
oShit="${RED}✧${RESET}"

### Cooler alternatives to colored indicators
# allOK="👌 "
# oShit="💩 "

# FQDN to lookup
FQDN_LOOKUP="google.com"

get_active_network_interfaces() {
    # Get the list of network services in the preferred order
    local services
    services=$(networksetup -listnetworkserviceorder | grep -o 'Device: [^)]*' | awk '{print $2}')

    # Iterate through each service and check its status using ifconfig
    for service in $services; do
        # Check if the device exists and is active
        if ifconfig "$service" >/dev/null 2>&1; then
            local status
            status=$(ifconfig "$service" | grep 'status:' | awk '{print $2}')
            if [ "$status" = "active" ]; then
                echo "$service"
            fi
        fi
    done
}

get_interface_details() {
    local interface=$1

    # Get the IP address and CIDR notation
    local ip_cidr
    ip_cidr=$(ifconfig -f inet:cidr "$interface" inet | grep 'inet ' | awk '{print $2}')
    local ip=${ip_cidr%/*}
    local cidr=${ip_cidr#*/}

    # Get the default gateway
    local gateway
    gateway=$(netstat -nr | grep 'default' | grep "$interface" | awk '{print $2}')

    # Ping the default gateway once
    if ping -t 1 -c 1 "$gateway" > /dev/null 2>&1; then
        gateway_status=$allOK
    else
        gateway_status=$oShit
    fi

    echo -e "Interface: $interface, IP: $ip/$cidr, Gateway: $gateway $gateway_status"
}

check_dns_servers() {
    local nameservers
    nameservers=$(grep -e "^nameserver" /etc/resolv.conf | awk '{ print $2 }')

    for nameserver in $nameservers; do
        echo -n "DNS: $nameserver "
        if nslookup "$FQDN_LOOKUP" "$nameserver" > /dev/null 2>&1; then
            echo -e "$allOK"  # Green star for success
        else
            echo -e "$oShit"  # Red star for failure
        fi
    done
}

main() {
    local active_interfaces
    active_interfaces=$(get_active_network_interfaces)

    for interface in $active_interfaces; do
        get_interface_details "$interface"
    done

    # Check DNS servers
    check_dns_servers
}

main
