#!/usr/bin/env python3
"""
SSH utility for quickly accessing configured hosts from ~/.ssh/config

This script retrieves hostnames and IP addresses from ~/.ssh/config, checks SSH connectivity,
and displays them with color-coded indicators (green for success, red for failure).
It supports parallel processing for efficient connectivity checks and sorts the output alphabetically.

For optimal performance, ensure ~/.ssh/config is correctly formatted with Host and HostName entries.
"""

# <xbar.title>SSH</xbar.title>
# <xbar.version>v1.3</xbar.version>
# <xbar.author>Jan Gronemann</xbar.author>
# <xbar.author.github>jandahl</xbar.author.github>
# <xbar.desc>Quickly SSH to your favorite hosts listed in your ~/.ssh/config file with status indicators.</xbar.desc>
#
# This script retrieves hostnames and IP addresses from ~/.ssh/config, checks SSH connectivity,
# and displays them in xbar with color-coded indicators (green for success, red for failure).
# It supports parallel processing for efficient connectivity checks and sorts the output alphabetically.
#
# Credits to the original concept by Thameera Senanayaka (github:thameera), enhanced and maintained by Jan Gronemann.

import os
import socket
import argparse
import logging
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
import configparser
import unittest

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants for font, colors, and icons
FONT = "size=18 font=UbuntuMono"
COLORS = {
    "red": "Crimson",
    "green": "ForestGreen"
}
ICONS = {
    "red": "✧",
    "green": "✦"
}
DEFAULT_SSH_CONFIG_PATH = os.path.expanduser("~/.ssh/config")
DEFAULT_SETTINGS_PATH = os.path.expanduser("~/.ssh/xbar-ssh-settings")
IGNORED_HOSTS = []

def load_settings(settings_path):
    """Load settings from the specified settings file."""
    global IGNORED_HOSTS
    config = configparser.ConfigParser()
    if os.path.exists(settings_path):
        config.read(settings_path)
        IGNORED_HOSTS = config.get("Settings", "ignored_hosts", fallback="").split()
    else:
        logging.warning(f"Settings file not found: {settings_path}")

def is_ignored(host):
    """Check if a host is in the ignored list."""
    return host in IGNORED_HOSTS

def check_ssh(ip):
    """Check SSH connectivity for a host IP."""
    try:
        with socket.create_connection((ip, 22), timeout=1):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False

def parse_ssh_config(ssh_config_path):
    """Parse the ~/.ssh/config file to retrieve hosts and their IP addresses."""
    hosts = {}
    if not os.path.exists(ssh_config_path):
        logging.error(f"SSH config file not found: {ssh_config_path}")
        return hosts

    with open(ssh_config_path, 'r') as f:
        lines = f.readlines()

    host = None
    for line in lines:
        line = line.strip()
        if line.startswith("Host "):
            host = line.split()[1]
            if host not in IGNORED_HOSTS:
                hosts[host] = {"ip": "", "comment": ""}
        elif host and host not in IGNORED_HOSTS:
            if line.startswith("HostName "):
                hosts[host]["ip"] = line.split()[1]
            elif line.startswith("#"):
                hosts[host]["comment"] = line

    return hosts

def display_results(hosts):
    """Display the SSH connectivity results."""
    output_lines = []
    any_success = False

    def process_host(host, ip):
        nonlocal any_success
        if ip and check_ssh(ip):
            status_icon = ICONS["green"]
            color = COLORS["green"]
            any_success = True
        else:
            status_icon = ICONS["red"]
            color = COLORS["red"]

        user_text = f"{host} - {ip}" if ip else host
        actions = f"color={color} bash=\"/usr/bin/open\" param1=\"-a\" param2=\"iterm\" param3=\"ssh://{host}\""
        return f"{status_icon} {user_text} | {FONT} {actions}"

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_host, host, data["ip"]) for host, data in hosts.items()]
        for future in futures:
            try:
                output_lines.append(future.result())
            except Exception as e:
                logging.error(f"Error processing host: {e}")

    output_lines.sort()
    header_line = "ssh" if any_success else "🚫ssh"
    return [header_line, "---"] + output_lines

@contextmanager
def handle_exceptions():
    """Context manager to handle exceptions gracefully."""
    try:
        yield
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        exit(1)

def main():
    """Main function to handle command-line arguments and execute the script."""
    parser = argparse.ArgumentParser(description="SSH utility for quickly accessing configured hosts from ~/.ssh/config")
    parser.add_argument('-i', '--input', type=str, help='Path to SSH config file', default=DEFAULT_SSH_CONFIG_PATH)
    parser.add_argument('-s', '--settings', type=str, help='Path to settings file', default=DEFAULT_SETTINGS_PATH)
    args = parser.parse_args()

    ssh_config_path = args.input
    settings_path = args.settings

    with handle_exceptions():
        load_settings(settings_path)
        hosts = parse_ssh_config(ssh_config_path)
        results = display_results(hosts)
        for line in results:
            print(line)
        exit(0)

class TestSSHUtility(unittest.TestCase):
    """Unit tests for the SSH utility script."""

    def test_is_ignored(self):
        self.assertTrue(is_ignored("host_to_ignore1"))
        self.assertFalse(is_ignored("some_other_host"))

    def test_check_ssh(self):
        self.assertFalse(check_ssh("192.0.2.0"))  # Non-routable IP address for testing

    def test_parse_ssh_config(self):
        hosts = parse_ssh_config(DEFAULT_SSH_CONFIG_PATH)
        self.assertIsInstance(hosts, dict)

    def test_display_results(self):
        hosts = {
            "test_host": {"ip": "192.0.2.0", "comment": ""}
        }
        results = display_results(hosts)
        self.assertIn("🚫ssh", results)

if __name__ == "__main__":
    main()
