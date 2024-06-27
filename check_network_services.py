#!/usr/bin/env python3

import argparse
import json
import os
import socket
import subprocess
import logging
from typing import List, Tuple

# Constants for indicators
DEFAULT_ALL_OK = "\033[32m✦\033[0m"
DEFAULT_O_SHIT = "\033[31m✧\033[0m"
FUN_MODE_ALL_OK = "👌"
FUN_MODE_O_SHIT = "💩"

# Global variables for indicators
ALL_OK = DEFAULT_ALL_OK
O_SHIT = DEFAULT_O_SHIT

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s')
logger = logging.getLogger()

def set_status_indicators(fun_mode: bool) -> None:
    """
    Set global status indicators based on whether fun mode is enabled.

    Args:
        fun_mode (bool): Whether fun mode is enabled.
    """
    global ALL_OK, O_SHIT
    if fun_mode:
        ALL_OK = FUN_MODE_ALL_OK
        O_SHIT = FUN_MODE_O_SHIT
    else:
        ALL_OK = DEFAULT_ALL_OK
        O_SHIT = DEFAULT_O_SHIT

def get_active_network_interfaces() -> List[str]:
    """
    Retrieve a list of active network interfaces. Cross-platform support for Linux, macOS, and Windows.

    Returns:
        List[str]: A list of active network interface names.
    """
    try:
        logger.debug("Getting list of network services")
        if os.name == "posix":
            if os.uname().sysname == "Darwin":
                services = subprocess.check_output(
                    ["networksetup", "-listnetworkserviceorder"], text=True
                )
                devices = [
                    line.split()[-1].strip(")")
                    for line in services.splitlines()
                    if "Device:" in line and line.split()[-1] != "Device: )"
                ]
            else:
                devices = subprocess.check_output(
                    ["ls", "/sys/class/net"], text=True
                ).splitlines()
        elif os.name == "nt":
            devices = subprocess.check_output(
                ["netsh", "interface", "show", "interface"], text=True
            ).splitlines()
            devices = [line.split()[-1] for line in devices if "Connected" in line]
        else:
            raise OSError("Unsupported operating system")

        logger.debug(f"Devices found: {devices}")
        active_interfaces = []
        for device in devices:
            logger.debug(f"Checking status of device: {device}")
            ifconfig_output = subprocess.run(
                ["ifconfig", device], capture_output=True, text=True
            )
            if "status: active" in ifconfig_output.stdout:
                logger.debug(f"Device {device} is active")
                active_interfaces.append(device)
            else:
                logger.debug(f"Device {device} is not active")
        logger.debug(f"Active interfaces: {active_interfaces}")
        return active_interfaces
    except subprocess.CalledProcessError as e:
        logger.error(f"Error getting network interfaces: {e}")
        return []

def get_interface_details(interface: str) -> Tuple[str, str, str]:
    """
    Retrieve the IP address, CIDR notation, and default gateway for a given interface.

    Args:
        interface (str): The network interface name.

    Returns:
        Tuple[str, str, str]: IP address, CIDR notation, and default gateway.
    """
    try:
        logger.debug(f"Getting IP and CIDR for interface: {interface}")
        ip_cidr_output = subprocess.check_output(["ifconfig", interface], text=True)
        logger.debug(f"ifconfig output for {interface}: {ip_cidr_output}")
        ip = None
        cidr = None
        for line in ip_cidr_output.splitlines():
            if "inet " in line:
                ip = line.split()[1]
                break
        if ip is None:
            raise ValueError("No IP address found for interface")
        
        # Attempt to get CIDR from netmask if available
        for line in ip_cidr_output.splitlines():
            if "netmask " in line:
                netmask = line.split("netmask ")[1].split()[0]
                cidr = sum([bin(int(x, 16)).count('1') for x in netmask.split(':')])
                break
        
        if cidr is None:
            raise ValueError("No CIDR notation found for interface")
        
        logger.debug(f"Getting gateway for interface: {interface}")
        gateway_output = subprocess.check_output(["netstat", "-nr"], text=True)
        logger.debug(f"netstat output: {gateway_output}")
        gateway = None
        for line in gateway_output.splitlines():
            if line.startswith("default") and interface in line:
                gateway = line.split()[1]
                break
        if gateway is None:
            raise ValueError("No gateway found for interface")
        logger.debug(f"Interface: {interface}, IP: {ip}, CIDR: {cidr}, Gateway: {gateway}")
        return ip, str(cidr), gateway
    except subprocess.CalledProcessError as e:
        logger.error(f"Error getting interface details for {interface}: {e}")
        return (None, None, None)
    except ValueError as e:
        logger.error(f"Error parsing interface details for {interface}: {e}")
        return (None, None, None)

def get_dhcp_server(interface: str) -> str:
    """
    Retrieve the DHCP server address for a given interface. Cross-platform support for Linux, macOS, and Windows.

    Args:
        interface (str): The network interface name.

    Returns:
        str: The DHCP server address.
    """
    try:
        logger.debug(f"Getting DHCP server for interface: {interface}")
        if os.name == "posix":
            if os.uname().sysname == "Darwin":
                dhcp_server = subprocess.check_output(
                    ["ipconfig", "getpacket", interface], text=True
                ).splitlines()
                for line in dhcp_server:
                    if "server_identifier" in line:
                        return line.split()[-1]
            else:
                dhcp_lease_file = f"/var/lib/dhcp/dhclient.{interface}.leases"
                if os.path.exists(dhcp_lease_file):
                    with open(dhcp_lease_file, 'r') as file:
                        for line in file:
                            if "dhcp-server-identifier" in line:
                                return line.split()[-1].strip(";")
                else:
                    raise FileNotFoundError(f"DHCP lease file not found for interface {interface}")
        elif os.name == "nt":
            dhcp_server = subprocess.check_output(
                ["netsh", "interface", "ip", "show", "config", "name=", interface], text=True
            ).splitlines()
            for line in dhcp_server:
                if "DHCP Server" in line:
                    return line.split(":")[-1].strip()
        else:
            raise OSError("Unsupported operating system")
        return "No DHCP server found"
    except subprocess.CalledProcessError as e:
        logger.error(f"Error getting DHCP server for {interface}: {e}")
        return "Error retrieving DHCP server"
    except FileNotFoundError as e:
        logger.error(f"Error finding DHCP lease file for {interface}: {e}")
        return "DHCP lease file not found"

def check_dns_servers(fqdn: str, terse: bool) -> List[dict]:
    """
    Check DNS servers for their resolution status of a given FQDN.

    Args:
        fqdn (str): The fully qualified domain name to lookup.
        terse (bool): Whether to use terse output format.

    Returns:
        List[dict]: List of DNS check results.
    """
    results = []
    try:
        with open("/etc/resolv.conf", "r") as file:
            lines = file.readlines()
        nameservers = [line.split()[1] for line in lines if line.startswith("nameserver")]
    except FileNotFoundError:
        nameservers = []

    for nameserver in nameservers:
        try:
            socket.gethostbyname(fqdn)
            status = ALL_OK
            status_text = "OK" if not terse else status
        except socket.error:
            status = O_SHIT
            status_text = "Failure" if not terse else status
        result = {"nameserver": nameserver, "status": status_text, "fqdn_queried": fqdn}
        results.append(result)
        if not terse:
            print(f"DNS: {nameserver} {status}")
    return results

def main() -> None:
    """
    Main function to execute the script logic based on command line arguments.
    """
    global DEBUG_MODE

    parser = argparse.ArgumentParser(description="Network and DNS Information Script")
    parser.add_argument("--interface", action="store_true", help="Output current interface")
    parser.add_argument("--ip", action="store_true", help="Output current IP")
    parser.add_argument("--ip-subnet", action="store_true", help="Output current IP and subnet")
    parser.add_argument("--gateway", action="store_true", help="Output current gateway")
    parser.add_argument("--dhcp", action="store_true", help="Output current DHCP server")
    parser.add_argument("--dns", action="store_true", help="Perform DNS tests")
    parser.add_argument("--fun-mode", action="store_true", help="Use fun mode with emojis")
    parser.add_argument("--fqdn", type=str, default="google.com", help="FQDN for DNS lookup")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    parser.add_argument("--terse", action="store_true", help="Use terse output format")

    args = parser.parse_args()

    # Set debug mode if the flag is provided
    DEBUG_MODE = args.debug
    if DEBUG_MODE:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # Set status indicators based on fun mode
    set_status_indicators(args.fun_mode)

    # If no specific flags are provided, output all information except IP (to avoid redundancy)
    if not (args.interface or args.ip or args.ip_subnet or args.gateway or args.dhcp or args.dns):
        args.interface = args.ip_subnet = args.gateway = args.dhcp = args.dns = True

    active_interfaces = get_active_network_interfaces()
    results = {"interfaces": [], "dns": []}

    for interface in active_interfaces:
        ip, cidr, gateway = get_interface_details(interface)
        if not ip or not cidr or not gateway:
            continue
        dhcp_server = get_dhcp_server(interface) if args.dhcp else None
        interface_result = {"interface": interface, "ip": ip, "cidr": cidr, "gateway": gateway, "dhcp_server": dhcp_server}
        results["interfaces"].append(interface_result)
        if not args.json and not args.terse:
            if args.interface:
                print(f"Interface: {interface}")
            if args.ip:
                print(f"IP: {ip}")
            if args.ip_subnet:
                print(f"IP/Subnet: {ip}/{cidr}")
            if args.gateway:
                gateway_status = ALL_OK
                try:
                    socket.create_connection((gateway, 80), timeout=1)
                except OSError:
                    gateway_status = O_SHIT
                print(f"Gateway: {gateway} {gateway_status}")
            if args.dhcp:
                print(f"DHCP Server: {dhcp_server}")

    if args.dns:
        dns_results = check_dns_servers(args.fqdn, args.terse)
        results["dns"].extend(dns_results)

    if args.json:
        print(json.dumps(results, indent=2))
    elif args.terse:
        terse_output = []
        for iface in results["interfaces"]:
            if args.gateway and not (args.interface or args.ip or args.ip_subnet):
                gateway_status = ALL_OK
                try:
                    socket.create_connection((iface["gateway"], 80), timeout=1)
                except OSError:
                    gateway_status = O_SHIT
                terse_output.append(f"gw: {iface['gateway']} {gateway_status}")
            else:
                if args.interface:
                    terse_output.append(f"if: {iface['interface']}")
                if args.ip or args.ip_subnet:
                    terse_output.append(f"ip: {iface['ip']}/{iface['cidr']}")
                if args.gateway:
                    gateway_status = ALL_OK
                    try:
                        socket.create_connection((iface["gateway"], 80), timeout=1)
                    except OSError:
                        gateway_status = O_SHIT
                    terse_output.append(f"gw: {iface['gateway']} {gateway_status}")
                if args.dhcp:
                    terse_output.append(f"dhcp: {iface['dhcp_server']}")
        for dns in results["dns"]:
            terse_output.append(f"dns: {dns['nameserver']} {dns['status']}")
        print("; ".join(terse_output))

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
