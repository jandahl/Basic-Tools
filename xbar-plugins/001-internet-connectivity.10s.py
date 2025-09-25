#!/usr/bin/env python3

from typing import Optional, Dict
import logging
import os
import re
import subprocess
import urllib.request

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Default constants
DEFAULT_PING_TIMEOUT = 1
DEFAULT_PING_ADDRESS = "1.1.1.1"
DEFAULT_YELLOW_THRESHOLD = 50

# Colors
colors = {
    "online": "Chartreuse",
    "offline": "Crimson",
    "error": "Crimson",
    "slow": "Gold"
}

# Read configuration from environment variables or use defaults
ping_timeout = int(os.getenv('PING_TIMEOUT', DEFAULT_PING_TIMEOUT))
ping_address = os.getenv('PING_ADDRESS', DEFAULT_PING_ADDRESS)
yellow_threshold = int(os.getenv('YELLOW_THRESHOLD', DEFAULT_YELLOW_THRESHOLD))

def perform_ping(address: str, timeout: int) -> Optional[str]:
    """
    Perform a ping and return the output.
    """
    try:
        result = subprocess.run(
            ["ping", "-c", "1", "-W", str(timeout), address],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        if result.returncode != 0:
            logging.error(f"Ping command failed with exit code {result.returncode}")
            return None
        return result.stdout
    except (subprocess.SubprocessError, OSError) as e:
        logging.error(f"Ping failed: {e}")
        return None

def parse_rtt(ping_output: str) -> Optional[float]:
    """
    Parse the RTT from the ping output.
    """
    patterns = [
        r'time=(\d+\.\d+)',  # Linux / Unix
        r'round-trip.* = (\d+\.\d+)',  # Generic
        r'mtime=(\d+\.\d+)',  # Possible variation
    ]
    for pattern in patterns:
        match = re.search(pattern, ping_output)
        if match:
            return float(match.group(1))
    logging.error("Failed to parse RTT from ping output")
    return None

def get_color_for_rtt(rtt: float, threshold: int) -> str:
    """
    Determine the color based on RTT.
    """
    return colors["online"] if rtt < threshold else colors["slow"]

def initialize() -> None:
    """
    Initialization function to setup the script.
    """
    logging.info("Initialization complete with the following settings:")
    logging.info(f"ping_timeout: {ping_timeout}")
    logging.info(f"ping_address: {ping_address}")
    logging.info(f"yellow_threshold: {yellow_threshold}")
    logging.info(f"colors: {colors}")

def main() -> None:
    """
    Main function to run the script logic.
    """
    initialize()

    ping_output = perform_ping(ping_address, ping_timeout)
    if ping_output is None:
        print(f"✧|color={colors['offline']} dropdown=false")
        print("---")
        print(f"No reply from {ping_address} within {ping_timeout} seconds")
        return

    rtt = parse_rtt(ping_output)
    if rtt is None:
        print(f"‽|color={colors['error']} dropdown=false")
        print("---")
        print("Error parsing RTT")
        return

    color = get_color_for_rtt(rtt, yellow_threshold)

    print(f"✦|color={color} dropdown=false")
    print("---")
    print(f"You're online (RTT: {rtt:.0f} ms)")

if __name__ == "__main__":
    main()
