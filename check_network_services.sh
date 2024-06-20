#!/bin/bash

# Constants for colors
GREEN="\033[32m"
RED="\033[31m"
RESET="\033[0m"

# Constants for indicators
GOOD_INDICATOR="${GREEN}✦${RESET}"
BAD_INDICATOR="${RED}✧${RESET}"

# FQDN to lookup
FQDN_LOOKUP="google.com"

# Functions

# Convert hexadecimal netmask to dotted-decimal format
hex_to_dotted_decimal() {
    local hexmask=$1
    local mask
    mask=$(printf "%d.%d.%d.%d\n" \
        $(( (0x${hexmask:2:2}) & 0xff )) \
        $(( (0x${hexmask:4:2}) & 0xff )) \
        $(( (0x${hexmask:6:2}) & 0xff )) \
        $(( (0x${hexmask:8:2}) & 0xff )))
    echo $mask
}

# Convert netmask to CIDR notation
netmask_to_cidr() {
    local netmask=$1
    local cidr=0
    IFS=.
    for octet in $netmask; do
        case $octet in
            255) cidr=$((cidr + 8));;
            254) cidr=$((cidr + 7));;
            252) cidr=$((cidr + 6));;
            248) cidr=$((cidr + 5));;
            240) cidr=$((cidr + 4));;
            224) cidr=$((cidr + 3));;
            192) cidr=$((cidr + 2));;
            128) cidr=$((cidr + 1));;
            0) ;;
            *) echo "Invalid netmask: $netmask"; exit 1;;
        esac
    done
    IFS=' '
    echo $cidr
}

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

    # Get the Local IP address
    local ip
    ip=$(ifconfig "$interface" | grep 'inet ' | awk '{print $2}' | head -n 1)

    # Get the netmask and convert to slash notation
    local hex_netmask
    hex_netmask=$(ifconfig "$interface" | grep 'inet ' | awk '{print $4}' | head -n 1)
    local netmask
    netmask=$(hex_to_dotted_decimal "$hex_netmask")
    local cidr
    cidr=$(netmask_to_cidr "$netmask")

    # Get the default gateway
    local gateway
    gateway=$(netstat -nr | grep 'default' | grep "$interface" | awk '{print $2}')

    # Ping the default gateway once
    if ping -c 1 -t 1 "$gateway" > /dev/null 2>&1; then
        gateway_status=$GOOD_INDICATOR
    else
        gateway_status=$BAD_INDICATOR
    fi

    echo -e "Interface: $interface, IP: $ip, Netmask: /$cidr, Gateway: $gateway $gateway_status"
}

check_dns_servers() {
    local nameservers
    nameservers=$(grep -e "^nameserver" /etc/resolv.conf | awk '{ print $2 }')

    for nameserver in $nameservers; do
        echo -n "DNS: $nameserver "
        if nslookup "$FQDN_LOOKUP" "$nameserver" > /dev/null 2>&1; then
            echo -e "$GOOD_INDICATOR"  # Green star for success
        else
            echo -e "$BAD_INDICATOR"  # Red star for failure
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
