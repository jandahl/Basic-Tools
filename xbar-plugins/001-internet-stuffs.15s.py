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
DNS_QUERY_DOMAIN = "example.com"
HTTP_TEST_URL = "http://example.com"
RIPE_WHOIS_SERVER = "whois.ripe.net"

# Status indicators with icons and colors
STATUS_INDICATORS = {
    "all_good": {"icon": "👌", "color": "ForestGreen"},
    "mostly_bad": {"icon": "⚠︎", "color": "DarkOrange"},
    "all_bad": {"icon": "💩", "color": "Crimson"},
}

# Test functions and their names
TESTS = {
    "ping_1": {"name": "Ping 1.1.1.1", "address": DEFAULT_PING_ADDRESS, "type": "ping"},
    "ping_gateway": {"name": "Ping Default Gateway", "type": "ping_gateway"},
    "dns_servers": {"name": "DNS Query", "type": "dns"},
    "http": {"name": "HTTP Request", "url": HTTP_TEST_URL, "type": "http"},
    "public_ip": {"name": "Public IP", "type": "public_ip"}
}

def run_command(command):
    return subprocess.run(command, capture_output=True, text=True, check=True).stdout.strip()

def get_default_gateway():
    try:
        result = run_command(["route", "-n", "get", "default"])
        for line in result.splitlines():
            if "gateway" in line:
                return line.split(":")[-1].strip()
    except subprocess.SubprocessError as e:
        logging.error(f"Error getting default gateway: {e}")
    return ""

def get_dns_servers():
    try:
        with open('/etc/resolv.conf') as f:
            return [line.split()[1] for line in f if line.strip().startswith('nameserver')]
    except Exception as e:
        logging.error(f"Error reading DNS servers: {e}")
    return []

def perform_ping(address, timeout):
    try:
        result = subprocess.run(["ping", "-c", "1", "-W", str(timeout), address], capture_output=True, text=True)
        if result.returncode == 0:
            return True
    except subprocess.SubprocessError as e:
        logging.error(f"Ping failed: {e}")
    return False

def query_dns(server, domain):
    try:
        socket.setdefaulttimeout(DEFAULT_PING_TIMEOUT)
        socket.gethostbyname_ex(domain)
        return True
    except socket.error as e:
        logging.error(f"DNS query failed: {e}")
    return False

def test_http(url):
    try:
        response = urllib.request.urlopen(url, timeout=DEFAULT_PING_TIMEOUT)
        return response.status == 200
    except Exception as e:
        logging.error(f"HTTP request failed: {e}")
    return False

def get_public_ip_info():
    try:
        public_ip = run_command(["curl", "-s", "https://icanhazip.com"])
        owner = query_ripe_whois(public_ip)
        return public_ip, owner
    except Exception as e:
        logging.error(f"Failed to get public IP info: {e}")
    return "Unknown", "Unknown"

def query_ripe_whois(ip):
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
            for line in response.decode('utf-8', errors='ignore').splitlines():
                if line.startswith(("descr:", "owner:", "inetnum:")):
                    return line.split(":", 1)[1].strip()
    except Exception as e:
        logging.error(f"RIPE WHOIS query failed: {e}")
    return "Unknown"

def check_network_conditions():
    gateway = get_default_gateway()
    return {
        "ping_1": perform_ping(DEFAULT_PING_ADDRESS, DEFAULT_PING_TIMEOUT),
        "ping_gateway": perform_ping(gateway, DEFAULT_PING_TIMEOUT) if gateway else False,
        "dns_servers": [query_dns(server, DNS_QUERY_DOMAIN) for server in get_dns_servers()],
        "http": test_http(HTTP_TEST_URL),
        "public_ip": get_public_ip_info(),
        "gateway_ip": gateway
    }

def determine_status(results):
    if not all([results["ping_1"], results["ping_gateway"], all(results["dns_servers"]), results["http"]]):
        return "mostly_bad"
    return "all_good"

def output_status(results, status):
    overall_icon = STATUS_INDICATORS[status]["icon"]
    overall_color = STATUS_INDICATORS[status]["color"]
    print(f"{overall_icon}|color={overall_color} dropdown=false")
    print("---")
    
    for test, data in TESTS.items():
        if test in ["ping_1", "ping_gateway", "http"]:
            success = results[test]
            name = data["name"]
            output = f"{name}: {'Success' if success else 'Failure'} | color={STATUS_INDICATORS['all_good' if success else 'all_bad']['color']}"
        elif test == "dns_servers":
            for idx, dns_success in enumerate(results[test]):
                name = data["name"]
                server = get_dns_servers()[idx]
                output = f"{name} ({server}): {'Success' if dns_success else 'Failure'} | color={STATUS_INDICATORS['all_good' if dns_success else 'all_bad']['color']}"
                print(output)
            continue
        elif test == "public_ip":
            ip, owner = results["public_ip"]
            output = f"Public IP: {ip} - Owner: {owner} | color={STATUS_INDICATORS['all_good']['color']}"
        print(output)

def main():
    try:
        results = check_network_conditions()
        status = determine_status(results)
        output_status(results, status)
    except Exception as e:
        logging.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
