#!/usr/bin/env python3

import os
import re
import subprocess
import socket
import logging
import urllib.request

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
    "green": {"icon": "👌 yeeeah", "color": "Chartreuse"},
    "red": {"icon": "💩 ohoo boy", "color": "Crimson"},
    "orange": {"icon": "🤷‍♂️ something's off", "color": "DarkOrange"},
    "yellow": {"icon": "🤷‍♂️ lookin' sketch'", "color": "Gold"}
}

def get_default_gateway() -> str:
    try:
        result = subprocess.run(
            ["route", "-n", "get", "default"],
            capture_output=True,
            text=True,
            check=False
        )
        for line in result.stdout.splitlines():
            if "gateway" in line:
                return line.split(":")[-1].strip()
    except subprocess.SubprocessError as e:
        logging.error(f"Error getting default gateway: {e}")
    return ""

def get_dns_servers() -> list:
    dns_servers = []
    try:
        with open('/etc/resolv.conf') as f:
            for line in f:
                if line.startswith('nameserver'):
                    dns_servers.append(line.split()[1])
    except Exception as e:
        logging.error(f"Error reading DNS servers: {e}")
    return dns_servers

def perform_ping(address: str, timeout: int) -> (bool, float):
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
    match = re.search(r'(\d+)% packet loss', ping_output)
    if match:
        return int(match.group(1))
    logging.error("Failed to parse packet loss from ping output")
    return 100

def parse_rtt(ping_output: str) -> float:
    match = re.search(r'round-trip min/avg/max/stddev = [\d.]+/([\d.]+)/', ping_output)
    if match:
        return float(match.group(1))
    logging.error("Failed to parse RTT from ping output")
    return None

def query_dns(server: str, domain: str) -> bool:
    try:
        socket.setdefaulttimeout(DEFAULT_PING_TIMEOUT)
        socket.gethostbyname_ex(domain)
        return True
    except socket.error as e:
        logging.error(f"DNS query failed: {e}")
    return False

def test_http(url: str) -> bool:
    try:
        response = urllib.request.urlopen(url, timeout=DEFAULT_PING_TIMEOUT)
        return response.status == 200
    except Exception as e:
        logging.error(f"HTTP request failed: {e}")
    return False

def get_public_ip_info() -> (str, str):
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
            
            owner = ""
            for line in response.decode("latin1").splitlines():
                if "descr:" in line.lower():
                    owner += line.split(":", 1)[1].strip() + ", "
            owner = owner[:-2]
            
            return owner
    except Exception as e:
        logging.error(f"RIPE WHOIS query failed: {e}")
    return "Unknown"

def check_network_conditions() -> dict:
    ping_success_1, rtt_1 = perform_ping(DEFAULT_PING_ADDRESS, DEFAULT_PING_TIMEOUT)
    gateway = get_default_gateway()
    ping_success_2, rtt_2 = perform_ping(gateway, DEFAULT_PING_TIMEOUT) if gateway else (False, 0.0)
    dns_servers = get_dns_servers()
    dns_success = all(query_dns(server, DNS_QUERY_DOMAIN) for server in dns_servers)
    http_success = test_http(HTTP_TEST_URL)
    public_ip, ip_owner = get_public_ip_info()
    
    return {
        "ping_1": ping_success_1,
        "ping_1_rtt": rtt_1,
        "ping_2": ping_success_2,
        "ping_2_rtt": rtt_2,
        "gateway_ip": gateway,
        "dns": dns_success,
        "dns_servers": dns_servers,
        "http": http_success,
        "public_ip": public_ip,
        "ip_owner": ip_owner
    }

def determine_status(results: dict) -> str:
    if not (results["ping_1"] and results["dns"] and results["http"]):
        return "red"
    elif results["ping_2"]:
        return "green"
    else:
        return "orange"

def color_for_rtt(rtt: float) -> str:
    if rtt < 50:
        return "green"
    elif rtt < 100:
        return "yellow"
    else:
        return "red"

def color_for_success(success: bool) -> str:
    return "green" if success else "red"

def output_status(results: dict, status: str):
    icon = STATUS_INDICATORS[status]["icon"]
    color = status  # Using the variable name directly
    print(f"{icon}|color={STATUS_INDICATORS[status]['color']} dropdown=false")
    print("---")
    
    if results['ping_1']:
        print(f"Ping {DEFAULT_PING_ADDRESS}: Success | color={color_for_rtt(results['ping_1_rtt'])}")
    else:
        print(f"Ping {DEFAULT_PING_ADDRESS}: Failure | color=red")
    
    if results['ping_2']:
        print(f"Ping Default Gateway ({results['gateway_ip']}): Success (RTT: {results['ping_2_rtt']:.2f} ms) | color={color_for_rtt(results['ping_2_rtt'])}")
    else:
        print(f"Ping Default Gateway ({results['gateway_ip']}): Failure | color=red")
    
    for dns_server in results["dns_servers"]:
        dns_success = query_dns(dns_server, DNS_QUERY_DOMAIN)
        print(f"DNS Query ({dns_server}): {'Success' if dns_success else 'Failure'} | color={color_for_success(dns_success)}")
        
    print(f"HTTP Request ({HTTP_TEST_URL}): {'Success' if results['http'] else 'Failure'} | color={color_for_success(results['http'])}")
    
    # WHOIS lookup colored as "green" if successful
    whois_owner = results['ip_owner']
    whois_color = "green" if whois_owner != "Unknown" else "red"
    print(f"Public IP: {results['public_ip']} - Owner: {whois_owner} | color={whois_color}")

def main():
    results = check_network_conditions()
    status = determine_status(results)
    output_status(results, status)

if __name__ == "__main__":
    main()
