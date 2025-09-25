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
import json
import atexit

RIPE_WHOIS_SERVER = "whois.ripe.net"
CACHE_FILE = "whois_cache.json"
cache = {}

# Load cache from file
def load_cache():
    global cache
    try:
        with open(CACHE_FILE, 'r') as f:
            cache = json.load(f)
    except FileNotFoundError:
        cache = {}

# Save cache to file
def save_cache():
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f)

# Register save_cache to be called on program exit
atexit.register(save_cache)

# Load the cache at the start
load_cache()

def query_ripe_whois(ip):
    if ip in cache:
        return cache[ip]
    
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
                if line.startswith("descr:"):
                    result = line.split(":", 1)[1].strip()
                    cache[ip] = result
                    return result
    except Exception as e:
        logging.error(f"RIPE WHOIS query failed: {e}")
    
    cache[ip] = "Unknown"
    return "Unknown"

def check_network_conditions():
    pass

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
