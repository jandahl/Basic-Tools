#!/usr/bin/env python3

import argparse
import socket
import http.client
import time

DEFAULT_HTTP_PORTS = ["80", "443"]
DEFAULT_NC_PORTS = [["22", "ssh"], ["23", "telnet"], ["80", "http"], ["443", "https"]]
SUCCESS_MESSAGE = 'Test succeeded.'
FAILURE_MESSAGE = 'Test failed.'

parser = argparse.ArgumentParser(description='Test network connectivity.')
parser.add_argument('target', metavar='TARGET', type=str, help='Hostname or IP address to test.')
parser.add_argument('-p', '--ports', metavar='PORTS', type=str, help='Comma-separated list of ports to test with netcat.')
parser.add_argument('-r', '--retry', metavar='SECONDS', type=int, default=0, help='Number of seconds to wait before retrying failed connections.')
args = parser.parse_args()

http_ports = DEFAULT_HTTP_PORTS if not args.ports else [p for p in args.ports.split(',')]
nc_ports = DEFAULT_NC_PORTS

try:
    ip_address = socket.gethostbyname(args.target)
    hostname = socket.gethostbyaddr(ip_address)[0]
    print(f'Target: {args.target} ({ip_address}, {hostname})')
except socket.gaierror:
    print(f'Error: Could not resolve hostname {args.target}')

for port in http_ports:
    if port == "80":
        conn = http.client.HTTPConnection(args.target, port=port, timeout=2)
    elif port == "443":
        conn = http.client.HTTPSConnection(args.target, port=port, timeout=2)
    print(f'Testing HTTP for port {port}...')
    try:
        conn.request("HEAD", "/")
        res = conn.getresponse()
        if res.status < 400:
            print(f'HTTP test for port {port} succeeded.')
        else:
            print(f'HTTP test for port {port} failed with status code {res.status}.')
        conn.close()
    except (http.client.HTTPException, ConnectionRefusedError, socket.timeout):
        print(f'HTTP test for port {port} failed.')
        if args.retry > 0:
            time.sleep(args.retry)

for port in nc_ports:
    if port[1]:
        print(f'Testing netcat for port {port[0]} ({port[1]})...')
    else:
        print(f'Testing netcat for port {port[0]}...')
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        sock.connect((args.target, int(port[0])))
        sock.close()
        print(f'Netcat test for port {port[0]} succeeded.')
    except (ConnectionRefusedError, socket.timeout):
        print(f'Netcat test for port {port[0]} failed.')
        if args.retry > 0:
            time.sleep(args.retry)
