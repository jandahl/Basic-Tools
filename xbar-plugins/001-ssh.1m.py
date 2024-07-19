#!/usr/bin/env python3
"""
SSH utility for quickly accessing configured hosts from ~/.ssh/config

This script retrieves hostnames and IP addresses from ~/.ssh/config, checks SSH connectivity,
and displays them with color-coded indicators (green for success, red for failure).
It supports parallel processing for efficient connectivity checks and sorts the output alphabetically.

For optimal performance, ensure ~/.ssh/config is correctly formatted with Host and HostName entries.
"""

# <xbar.title>SSH</xbar.title>
# <xbar.version>v1.4</xbar.version>
# <xbar.author>Jan Gronemann</xbar.author>
# <xbar.author.github>YourGitHubUsername</xbar.author.github>
# <xbar.desc>Quickly SSH to your favorite hosts listed in your ~/.ssh/config file with status indicators.</xbar.desc>

import os
import socket
import argparse
import logging
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
import configparser
import subprocess
import unittest

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Default constants
DEFAULT_SSH_CONFIG_PATH = os.path.expanduser("~/.ssh/config")
DEFAULT_SETTINGS_PATH = os.path.expanduser("~/.config/xbar/ssh-config")
DEFAULT_FONT = "size='24' font='Courier New'"
DEFAULT_COLORS = {
    "red": "Crimson",
    "green": "ForestGreen"
}
DEFAULT_ICONS = {
    "red": "✧",
    "green": "✦",
    "active": "🌐"
}
DEFAULT_TERMINAL = "Terminal"

# Global settings
FONT = DEFAULT_FONT
COLORS = DEFAULT_COLORS
ICONS = DEFAULT_ICONS
TERMINAL = DEFAULT_TERMINAL
IGNORED_HOSTS = []

def ensure_directory_exists(path):
    """Ensure the directory for the given path exists."""
    directory = os.path.dirname(path)
    if not os.path.exists(directory):
        os.makedirs(directory)

def load_settings(settings_path):
    """Load settings from the specified settings file."""
    global FONT, COLORS, ICONS, TERMINAL, IGNORED_HOSTS
    ensure_directory_exists(settings_path)
    config = configparser.ConfigParser()
    if os.path.exists(settings_path):
        config.read(settings_path)
        FONT = config.get("Appearance", "font", fallback=DEFAULT_FONT)
        COLORS["red"] = config.get("Colors", "red", fallback=DEFAULT_COLORS["red"])
        COLORS["green"] = config.get("Colors", "green", fallback=DEFAULT_COLORS["green"])
        TERMINAL = config.get("General", "terminal", fallback=DEFAULT_TERMINAL)
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

def check_active_ssh(host):
    """Check if there are any active SSH connections to the host."""
    try:
        result = subprocess.run(['ps', 'aux'], stdout=subprocess.PIPE)
        processes = result.stdout.decode('utf-8')
        return f"ssh {host}" in processes
    except Exception as e:
        logging.error(f"Error checking active SSH connections: {e}")
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
            if "*" in host or "?" in host:
                continue
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
            status_icon = ICONS["active"] if check_active_ssh(host) else ICONS["green"]
            color = COLORS["green"]
            any_success = True
        else:
            status_icon = ICONS["red"]
            color = COLORS["red"]

        user_text = f"{host} - {ip}" if ip else host
        actions = f"color={color} bash=\"/usr/bin/open\" param1=\"-a\" param2=\"{TERMINAL}\" param3=\"ssh://{host}\""
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

def create_script_config(output_file):
    """Create a sample script configuration file."""
    sample_config = """
# Script defaults to read this from ~/.config/xbar/ssh-config
[Appearance]
# Example change font size and use this font: https://fonts.google.com/specimen/Kode+Mono
font = size=18 font='Kode Mono'

[Colors]
red = Crimson
green = ForestGreen

[General]
# Options: Terminal, iterm
terminal = Terminal

[Settings]
ignored_hosts = host_to_ignore1 host_to_ignore2
"""
    if output_file == "-":
        print(sample_config)
    else:
        if os.path.exists(output_file):
            raise FileExistsError(f"Config file already exists: {output_file}")
        ensure_directory_exists(output_file)
        with open(output_file, 'w') as f:
            f.write(sample_config)
        print(f"Sample config file created at: {output_file}")

def main():
    """Main function to handle command-line arguments and execute the script."""
    parser = argparse.ArgumentParser(description="SSH utility for quickly accessing configured hosts from ~/.ssh/config")
    parser.add_argument('-i', '--input', type=str, help='Path to SSH config file', default=DEFAULT_SSH_CONFIG_PATH)
    parser.add_argument('-s', '--settings', type=str, help='Path to settings file', default=DEFAULT_SETTINGS_PATH)
    parser.add_argument('--create-script-config', type=str, nargs='?', const=DEFAULT_SETTINGS_PATH,
                        help='Create a sample configuration file. Use "-" to print to screen.')
    args = parser.parse_args()

    if args.create_script_config is not None:
        try:
            create_script_config(args.create_script_config)
        except FileExistsError as e:
            print(e)
        exit(0)

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
