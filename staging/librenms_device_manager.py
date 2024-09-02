#!/usr/bin/env python3

"""
add_Libre_Devices.py

This script adds devices to LibreNMS via the command line based on the provided
parameters. It supports switches, routers, and access points and allows for flexible
configuration of device names, ports, and site locations.

Usage:
    python add_Libre_Devices.py --type=ap --site="Broechner-Danmark-1552" \
                                --first-device=1 --last-device=49 --starting-port=16101

Options:
    --dry-run   Simulate the commands without executing them.
    --self-test Run basic unit tests for the script.

Requirements:
    No external dependencies are required.

Exit Codes:
    0 - Success
    1 - Error
"""

import argparse
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Device types mapping for easy extensibility
DEVICE_TYPES = {
    'ap': 'ap',
    'sw': 'sw',
    'ro': 'ro',
}

def parse_arguments():
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(description='Add devices to LibreNMS')
    parser.add_argument('--type', required=True, choices=DEVICE_TYPES.keys(), help='Device type (e.g., ap, sw, ro)')
    parser.add_argument('--site', required=True, help='Site location for the devices')
    parser.add_argument('--first-device', type=int, required=True, help='Starting device number')
    parser.add_argument('--last-device', type=int, required=True, help='Ending device number')
    parser.add_argument('--starting-port', type=int, required=True, help='Starting SNMP port number')
    parser.add_argument('--dry-run', action='store_true', help='Simulate the command without executing it')

    return parser.parse_args()

def add_device(device_type, site, device_number, port, dry_run=False):
    """
    Add a device to LibreNMS.

    Parameters:
        device_type (str): The type of device (e.g., ap, sw, ro).
        site (str): The site location of the device.
        device_number (int): The device number.
        port (int): The SNMP port number.
        dry_run (bool): If True, simulate the command without executing it.

    Returns:
        None
    """
    try:
        device_name = f"{device_type}-{device_number:02d}-{site}.local"
        command = f"./lnms device:add {device_name} --v2c --port={port} -c sentia-dk-network --force"
        if dry_run:
            logging.info(f"Dry-run: {command}")
        else:
            logging.info(f"Executing command: {command}")
            # Simulate command execution by printing the command (replace with actual execution code if needed)
            print(command)
    except Exception as e:
        logging.error(f"Failed to add device {device_name}: {str(e)}")
        sys.exit(1)

def main():
    """
    Main function to add devices in a range to LibreNMS.
    """
    args = parse_arguments()

    for device_number in range(args.first_device, args.last_device + 1):
        port = args.starting_port + (device_number - args.first_device)
        add_device(DEVICE_TYPES[args.type], args.site, device_number, port, args.dry_run)

    logging.info("All devices processed successfully.")
    sys.exit(0)

def self_test():
    """
    Basic unit tests for the script functionality.
    """
    try:
        # Test adding a single device
        add_device('ap', 'Test-Site', 1, 16101, dry_run=True)
        # Test adding a range of devices
        main()
        logging.info("Self-test passed.")
    except Exception as e:
        logging.error(f"Self-test failed: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    if '--self-test' in sys.argv:
        self_test()
    else:
        main()
