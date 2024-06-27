#!/usr/bin/env python3

"""
Script Name: internet_stuffs.py
Author: Jan Gronemann
Created: 2024-06-25
Last Modified: 2024-06-27
Description: This xbar script checks various network conditions and displays the status in the top bar.
"""

import subprocess
import socket
import logging
import urllib.request
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Default constants
DEFAULT_PING_TIMEOUT = 1
DEFAULT_PING_ADDRESS = "1.1.1.1"
DEFAULT_YELLOW_THRESHOLD = 50
DNS_QUERY_DOMAIN = "example.com"
HTTP_TEST_URL = "http://example.com"
RIPE_WHOIS_SERVER = "whois.ripe.net"

# Status indicators with icons and colors
STATUS_INDICATORS = {
    "all_good": {"icon": "👌 yeeeah", "color": "Chartreuse"},
    "all_bad": {"icon": "💩 ohoo boy", "color": "Crimson"},
    "mostly_bad": {"icon": "🤐 something's quite off", "color": "DarkOrange"},
    "mostly_good": {"icon": "🤷‍♂️ lookin' sketch'", "color": "Gold"}
}

# Test functions and their names
TESTS = {
    "ping_1": {"name": "Ping 1.1.1.1", "good_format": "Ping 1.1.1.1: Success", "bad_format": "Ping 1.1.1.1: Failure"},
    "ping_gateway": {"name": "Ping Default Gateway", "good_format": "Ping Default Gateway ({gateway}): Success", "bad_format": "Ping Default Gateway ({gateway}): Failure"},
    "dns_servers": {"name": "DNS Query", "good_format": "DNS Query ({server}): Success", "bad_format": "DNS Query ({server}): Failure"},
    "http": {"name": "HTTP Request", "good_format": "HTTP Request ({url}): Success", "bad_format": "HTTP Request ({url}): Failure"},
    "public_ip": {"name": "Public IP", "good_format": "Public IP: {ip} - Owner: {owner}", "bad_format": "Public IP: {ip} - Owner: {owner}"}
}

def get_default_gateway() -> str:
    """
    Get the default gateway of the primary network interface.
    
    :return: The default gateway IP address.
    """
    try:
        result = subprocess.run(
            ["route", "-n", "get", "default"],
            capture_output=True,
            text=True,
            check=True
        )
        for line in result.stdout.splitlines():
            if "gateway" in line:
                return line.split(":")[-1].strip()
    except subprocess.SubprocessError as e:
        logging.error(f"Error getting default gateway: {e}")
    return ""

def get_dns_servers() -> list:
    """
    Get the DNS servers configured on the system.
    
    :return: A list of DNS server IP addresses.
    """
    dns_servers = []
    try:
        with open('/etc/resolv.conf') as f:
            for line in f:
                if line.strip().startswith('nameserver'):
                    dns_servers.append(line.split()[1])
    except Exception as e:
        logging.error(f"Error reading DNS servers: {e}")
    return dns_servers

def perform_ping(address: str, timeout: int) -> (bool, float):
    """
    Perform a ping and return if it was successful and the RTT.
    
    :param address: The IP address to ping.
    :param timeout: Timeout for the ping command.
    :return: A tuple (success: bool, RTT: float).
    """
    try:
        result = subprocess.run(
            ["ping", "-c", "1", "-W", str(timeout), address],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            packet_loss = parse_packet_loss(result.stdout)
            rtt = parse_rtt(result.stdout)
            if packet_loss == 0 and rtt is not None:
                return True, rtt
    except subprocess.SubprocessError as e:
        logging.error(f"Ping failed: {e}")
    return False, 0.0

def parse_packet_loss(ping_output: str) -> int:
    """
    Parse the packet loss from the ping output.
    
    :param ping_output: The output of the ping command.
    :return: The packet loss percentage.
    """
    match = re.search(r'(\d+)% packet loss', ping_output)
    if match:
        return int(match.group(1))
    logging.error("Failed to parse packet loss from ping output")
    return 100

def parse_rtt(ping_output: str) -> float:
    """
    Parse the RTT from the ping output.
    
    :param ping_output: The output of the ping command.
    :return: The RTT in milliseconds.
    """
    match = re.search(r'round-trip min/avg/max/stddev = [\d.]+/([\d.]+)/', ping_output)
    if match:
        return float(match.group(1))
    logging.error("Failed to parse RTT from ping output")
    return None

def query_dns(server: str, domain: str) -> bool:
    """
    Query a DNS server for a domain.
    
    :param server: The DNS server IP address.
    :param domain: The domain to query.
    :return: True if the query is successful, False otherwise.
    """
    try:
        socket.setdefaulttimeout(DEFAULT_PING_TIMEOUT)
        socket.gethostbyname_ex(domain)
        return True
    except socket.error as e:
        logging.error(f"DNS query failed: {e}")
    return False

def test_http(url: str) -> bool:
    """
    Test an HTTP request to a given URL.
    
    :param url: The URL to request.
    :return: True if the request is successful, False otherwise.
    """
    try:
        response = urllib.request.urlopen(url, timeout=DEFAULT_PING_TIMEOUT)
        return response.status == 200
    except Exception as e:
        logging.error(f"HTTP request failed: {e}")
    return False

def get_public_ip_info() -> (str, str):
    """
    Get the current public IP address and its owner using a simple curl command.
    
    :return: A tuple (public_ip: str, owner: str).
    """
    try:
        public_ip = subprocess.run(
            ["curl", "-s", "https://icanhazip.com"],
            capture_output=True,
            text=True,
            check=True
        ).stdout.strip()

        owner = query_ripe_whois(public_ip)
        return public_ip, owner
    except Exception as e:
        logging.error(f"Failed to get public IP info: {e}")
    return "Unknown", "Unknown"

def query_ripe_whois(ip: str) -> str:
    """
    Query RIPE WHOIS service to find the owner of an IP address.
    
    :param ip: The IP address to query.
    :return: The owner information fetched from WHOIS.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((RIPE_WHOIS_SERVER, 43))
            s.sendall(f"-B {ip}\n".encode())
            response = b""
            while True:
                data = s.recv(1024)
                if not data:
                    break
                response += data
            
            # Attempt to extract owner information from WHOIS response
            owner = ""
            lines = response.decode('utf-8', errors='ignore').splitlines()
            for line in lines:
                if line.startswith("descr:"):
                    owner = line.split(":", 1)[1].strip()
                    break
                elif line.startswith("owner:"):
                    owner = line.split(":", 1)[1].strip()
                    break
                elif line.startswith("inetnum:"):
                    owner = line.split(":", 1)[1].strip()
                    break
            
            return owner
    except Exception as e:
        logging.error(f"RIPE WHOIS query failed: {e}")
    return "Unknown"

def check_network_conditions() -> dict:
    """
    Check the various network conditions and return the results.
    
    :return: A dictionary with the results of the network tests.
    """
    ping_1_success, ping_1_rtt = perform_ping(DEFAULT_PING_ADDRESS, DEFAULT_PING_TIMEOUT)
    gateway = get_default_gateway()
    ping_gateway_success, ping_gateway_rtt = perform_ping(gateway, DEFAULT_PING_TIMEOUT) if gateway else (False, 0.0)
    dns_servers = get_dns_servers()
    http_success = test_http(HTTP_TEST_URL)
    public_ip, ip_owner = get_public_ip_info()
    
    return {
        "ping_1": ping_1_success,
        "ping_gateway": ping_gateway_success,
        "dns_servers": dns_servers,
        "http": http_success,
        "public_ip": public_ip,
        "ip_owner": ip_owner,
        "gateway_ip": gateway
    }

def determine_status(results: dict) -> str:
    """
    Determine the overall network status based on the results of the tests.
    
    :param results: The dictionary containing the results of the network tests.
    :return: The status key indicating the overall network status.
    """
    if not all([
        results["ping_1"],
        results["ping_gateway"],
        all(query_dns(server, DNS_QUERY_DOMAIN) for server in results["dns_servers"]),
        results["http"]
    ]):
        return "mostly_bad"
    
    return "all_good"

def output_status(results: dict, status: str):
    """
    Output the status of each network test and the overall status.
    
    :param results: The dictionary containing the results of the network tests.
    :param status: The key indicating the overall network status.
    """
    overall_icon = STATUS_INDICATORS[status]["icon"]
    overall_color = STATUS_INDICATORS[status]["color"]
    print(f"{overall_icon}|color={overall_color} dropdown=false")
    print("---")
    
    for test, test_data in TESTS.items():
        if test == "ping_1":
            if results[test]:
                print(f"{test_data['good_format']} | color={STATUS_INDICATORS['all_good']['color']}")
            else:
                print(f"{test_data['bad_format']} | color={STATUS_INDICATORS['all_bad']['color']}")
        elif test == "ping_gateway":
            if results[test]:
                print(f"{test_data['good_format'].format(gateway=results['gateway_ip'])} | color={STATUS_INDICATORS['all_good']['color']}")
            else:
                print(f"{test_data['bad_format'].format(gateway=results['gateway_ip'])} | color={STATUS_INDICATORS['all_bad']['color']}")
        elif test == "dns_servers":
            for server in results[test]:
                result = query_dns(server, DNS_QUERY_DOMAIN)
                if result:
                    print(f"{test_data['good_format'].format(server=server)} | color={STATUS_INDICATORS['all_good']['color']}")
                else:
                    print(f"{test_data['bad_format'].format(server=server)} | color={STATUS_INDICATORS['all_bad']['color']}")
        elif test == "http":
            if results[test]:
                print(f"{test_data['good_format'].format(url=HTTP_TEST_URL)} | color={STATUS_INDICATORS['all_good']['color']}")
            else:
                print(f"{test_data['bad_format'].format(url=HTTP_TEST_URL)} | color={STATUS_INDICATORS['all_bad']['color']}")
        elif test == "public_ip":
            print(f"{test_data['good_format'].format(ip=results['public_ip'], owner=results['ip_owner'])} | color={STATUS_INDICATORS['all_good']['color']}")

def main():
    """
    Main function to execute network checks and output status.
    """
    try:
        network_results = check_network_conditions()
        network_status = determine_status(network_results)
        output_status(network_results, network_status)
    except Exception as e:
        logging.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()