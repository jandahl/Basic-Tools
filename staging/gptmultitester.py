#!/usr/bin/env python3

# I would like a Python 3 script that has a prepulated multidimensional array with PORT NUMBER and PORT USAGE, e.g. "80","http";"443","https". The script should expect a target host or IPv4 address as a command line argument and give a help screen if it does not receive one. If it receives a valid command line argument, it should then proceed to: 1) Output the target on screen and do a DNS A lookup/reverse PTR lookup and print this in a parenthesis. 2) Try to reach the given target using conn.request, given a separate multidimensional array. 3) For each member of its multidimensional array it should try to reach it via raw sockets. The script should accept several hostnames and/or IPs. Also, I should like to be able to serve this script command line arguments that add port numbers to either conn.request (e.g. "-c 123,456" or "--curl 123,456") or raw sockets (e.g. "-p 789,123" or "--ports 789,123"), and an option for a retry timer in seconds (e.g. "-r 10" or "--retry 10"). Failure and success messages should be abstracted to variables that can be shared and should be in the form of emojis. Use try/catch to avoid crashes.

import argparse
import socket
import http.client

# Define the multidimensional array with port numbers and port usage
port_array = [["80", "http"], ["443", "https"], ["8080", "http-alt"]]

# Define variables for success and failure messages
success_emoji = "✅"
failure_emoji = "❌"

# Define a function to connect to a host using raw sockets
def connect_to_port(host, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((host, int(port)))
        s.shutdown(socket.SHUT_RDWR)
        return True
    except:
        return False

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Check ports on a target host.')
parser.add_argument('host', type=str, help='the target host or IPv4 address')
parser.add_argument('-c', '--curl', type=str, help='comma-separated list of cURL port numbers')
parser.add_argument('-p', '--ports', type=str, help='comma-separated list of netcat port numbers')
parser.add_argument('-r', '--retry', type=int, default=0, help='number of seconds to wait before retrying failed ports')
args = parser.parse_args()

# Perform DNS A lookup/reverse PTR lookup and print the result
try:
    ip_address = socket.gethostbyname(args.host)
    hostname = socket.gethostbyaddr(ip_address)[0]
    print(args.host + " (" + ip_address + ")")
except:
    print("Error: unable to perform DNS lookup for " + args.host)
    exit()

# Try to reach the target using conn.request
try:
    conn = http.client.HTTPConnection(args.host)
    conn.request("HEAD", "/")
    response = conn.getresponse()
    if response.status >= 200 and response.status < 300:
        print(success_emoji + " Target reached via HTTP on port 80")
    else:
        print(failure_emoji + " Unable to reach target via HTTP on port 80")
except:
    print(failure_emoji + " Unable to reach target via HTTP on port 80")

# Try to connect to each port using raw sockets
for port in port_array:
    if connect_to_port(args.host, port[0]):
        print(success_emoji + " " + port[1] + " service detected on port " + port[0])
    elif args.retry > 0:
        print(failure_emoji + " " + port[1] + " service not detected on port " + port[0] + ", retrying in " + str(args.retry) + " seconds...")
        time.sleep(args.retry)
        if connect_to_port(args.host, port[0]):
            print(success_emoji + " " + port[1] + " service detected on port " + port[0])
        else:
            print(failure_emoji + " " + port[1] + " service not detected on port " + port[0])
    else:
        print(failure_emoji + " " + port[1] + " service not detected on port " + port[0])

# Handle additional command-line arguments for cURL and netcat ports
if args.curl:
    for curl_port in args.curl.split(","):
        if connect_to_port(args.host, curl_port):
            print(success_emoji + " cURL service detected on port " + curl_port)
        else:
            print(failure_emoji + " cURL service not detected on port " + curl_port)

if args.ports:
    for netcat_port in args.ports.split(","):
        if connect_to_port(args.host, netcat_port):
            print(success_emoji + " netcat service detected on port " + netcat_port)
        else:
            print(failure_emoji + " netcat service not detected on port " + netcat_port)
