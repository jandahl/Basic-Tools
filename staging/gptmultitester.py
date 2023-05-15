#!/usr/bin/env python3

# I would like a Python 3 script that has a prepulated multidimensional array with PORT NUMBER and PORT USAGE, e.g. "80","http";"443","https". The script should expect a target host or IPv4 address as a command line argument and give a help screen if it does not receive one. If it receives a valid command line argument, it should then proceed to: 1) Output the target on screen and do a DNS A lookup/reverse PTR lookup and print this in a parenthesis. 2) Try to reach the given target using conn.request, given a separate multidimensional array. 3) For each member of its multidimensional array it should try to reach it via raw sockets. The script should accept several hostnames and/or IPs. Also, I should like to be able to serve this script command line arguments that add port numbers to either conn.request (e.g. "-c 123,456" or "--curl 123,456") or raw sockets (e.g. "-p 789,123" or "--ports 789,123"), and an option for a retry timer in seconds (e.g. "-r 10" or "--retry 10"). Failure and success messages should be abstracted to variables that can be shared and should be in the form of emojis. Use try/catch to avoid crashes.

import argparse
import socket
import http.client
import time

# Multidimensional array of port numbers and usage
PORTS = [("80", "http"), ("443", "https"), ("22", "ssh")]

# Failure and success messages with emojis
SUCCESS_MESSAGE = "✅ Success!"
FAILURE_MESSAGE = "❌ Failure!"

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Test script to check port availability.')
    parser.add_argument('targets', metavar='TARGET', type=str, nargs='+', help='Target host or IPv4 address')
    parser.add_argument('-c', '--curl', metavar='PORTS', type=str, help='Port numbers to use for HTTP requests')
    parser.add_argument('-p', '--ports', metavar='PORTS', type=str, help='Port numbers to use for raw socket connections')
    parser.add_argument('-r', '--retry', metavar='SECONDS', type=int, default=0, help='Retry timer in seconds')
    args = parser.parse_args()

    # Check if target argument was provided
    if not args.targets:
        parser.print_help()
        exit()

    # Parse additional port arguments
    curl_ports = [int(p) for p in args.curl.split(',')] if args.curl else []
    raw_ports = [int(p) for p in args.ports.split(',')] if args.ports else []

    # Loop through targets
    for target in args.targets:
        try:
            # DNS resolution and reverse PTR lookup
            ip = socket.gethostbyname(target)
            name = socket.gethostbyaddr(ip)[0]
            print(f"{target} ({ip})")

            # HTTP requests using http.client
            conn = http.client.HTTPConnection(target)
            conn.request("GET", "/")
            response = conn.getresponse()
            print(f"HTTP response: {response.status} {response.reason}")
            conn.close()

            # Raw socket connections
            for port, usage in PORTS:
                if port in raw_ports:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(2)
                    result = s.connect_ex((target, int(port)))
                    if result == 0:
                        print(f"Port {port} ({usage}): {SUCCESS_MESSAGE}")
                    else:
                        print(f"Port {port} ({usage}): {FAILURE_MESSAGE}")
                    s.close()

            # HTTP requests with custom ports
            for port in curl_ports:
                conn = http.client.HTTPConnection(target, port)
                conn.request("GET", "/")
                response = conn.getresponse()
                print(f"HTTP response (port {port}): {response.status} {response.reason}")
                conn.close()

        except socket.gaierror:
            print(f"{target}: {FAILURE_MESSAGE}")

        if args.retry:
            time.sleep(args.retry)

if __name__ == '__main__':
    main()
