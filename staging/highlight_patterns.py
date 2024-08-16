#!/usr/bin/env python3
"""
This script reads input from stdin, highlights lines matching specific regex patterns with specified colors, and outputs the result to stdout.

Example usage:
    ./highlight_patterns.py --create-configs
    cat input.txt | ./highlight_patterns.py -o output.txt --config-dir ~/.config/highlight_patterns
    cat input.txt | ./highlight_patterns.py -o output.txt --theme default
    cat input.txt | ./highlight_patterns.py -o output.txt --theme-file /path/to/another_theme.json
"""

import re
import sys
import argparse
import logging
import unittest
import json
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Default config directory
CONFIG_DIR = Path.home() / ".config" / "highlight_patterns"

EXAMPLE_THEME = {
    'default': {
        'red': "\033[1;37;41m",
        'green': "\033[37;42m",
        'reset': "\033[0m"
    }
}

EXAMPLE_PATTERN_FILES = {
    'highlight-001-green.json': {
        'patterns': [
            r'\b0% packet loss\b'
        ]
    },
    'highlight-002-red.json': {
        'patterns': [
            r'\b\d+% packet loss\b'
        ]
    }
}

def load_themes(theme_file: Path) -> dict:
    """
    Loads color themes from the theme JSON file.

    Args:
        theme_file (Path): Path to the theme JSON file.

    Returns:
        dict: A dictionary of color themes.
    """
    try:
        with theme_file.open('r') as file:
            return json.load(file)
    except json.JSONDecodeError as e:
        logging.error(f"Error reading theme file {theme_file}: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error loading theme file {theme_file}: {e}")
        sys.exit(1)

def load_patterns(config_dir: Path, themes: dict) -> list:
    """
    Loads regex patterns and their corresponding colors from config files.

    Args:
        config_dir (Path): Path to the configuration directory.
        themes (dict): A dictionary of color themes.

    Returns:
        list: A list of tuples containing compiled regex patterns and their corresponding ANSI color codes.
    """
    pattern_files = sorted(config_dir.glob("highlight-*.json"))
    patterns = []

    for pattern_file in pattern_files:
        try:
            with pattern_file.open('r') as file:
                config = json.load(file)
                color_name = pattern_file.stem.split('-')[-1]
                color_code = themes.get(color_name)
                if color_code:
                    for pattern in config['patterns']:
                        patterns.append((re.compile(pattern), color_code))
                else:
                    logging.warning(f"Color '{color_name}' not found in themes.")
        except json.JSONDecodeError as e:
            logging.error(f"Error reading pattern file {pattern_file}: {e}")
        except Exception as e:
            logging.error(f"Error loading pattern file {pattern_file}: {e}")

    return patterns

def highlight_line(line: str, patterns: list, reset_color: str) -> str:
    """
    Highlights parts of a given line if they match any of the provided patterns.

    Args:
        line (str): The input line to highlight.
        patterns (list): A list of tuples containing regex patterns and their corresponding ANSI color codes.
        reset_color (str): The ANSI color code to reset the color.

    Returns:
        str: The line with highlighted matches if any are found, otherwise the original line.
    """
    for regex, color in patterns:
        if regex.search(line):
            line = regex.sub(lambda match: f"{color}{match.group(0)}{reset_color}", line)
            break  # Stop after the first match
    return line

def process_input(input_stream, output_stream, patterns: list, reset_color: str) -> None:
    """
    Processes the input stream, highlights matching parts of lines, and writes the result to the output stream.

    Args:
        input_stream: The input stream to read from.
        output_stream: The output stream to write to.
        patterns (list): A list of tuples containing regex patterns and their corresponding ANSI color codes.
        reset_color (str): The ANSI color code to reset the color.
    """
    line_count = 0
    match_count = 0

    for line in input_stream:
        line = line.rstrip()  # Remove any trailing newline characters
        try:
            highlighted_line = highlight_line(line, patterns, reset_color)
            if line != highlighted_line:
                match_count += 1
            output_stream.write(highlighted_line + '\n')
            line_count += 1
        except Exception as e:
            logging.error(f"Error processing line: {line}. Error: {e}")

    logging.info(f"Processed {line_count} lines with {match_count} matches.")

def create_example_configs(config_dir: Path) -> None:
    """
    Creates example configuration files in the specified directory.

    Args:
        config_dir (Path): Path to the configuration directory.
    """
    config_dir.mkdir(parents=True, exist_ok=True)

    theme_file = config_dir / "theme.json"
    if theme_file.exists():
        overwrite = input(f"Theme file {theme_file} already exists. Overwrite? (y/n): ")
        if overwrite.lower() != 'y':
            print("Skipping theme file creation.")
            return
    with theme_file.open('w') as file:
        json.dump(EXAMPLE_THEME, file, indent=4)
    print(f"Created theme file: {theme_file}")

    for filename, content in EXAMPLE_PATTERN_FILES.items():
        pattern_file = config_dir / filename
        if pattern_file.exists():
            overwrite = input(f"Pattern file {pattern_file} already exists. Overwrite? (y/n): ")
            if overwrite.lower() != 'y':
                print(f"Skipping pattern file creation: {pattern_file}")
                continue
        with pattern_file.open('w') as file:
            json.dump(content, file, indent=4)
        print(f"Created pattern file: {pattern_file}")

def main() -> None:
    """
    Main function to parse command-line arguments and run the script.
    """
    parser = argparse.ArgumentParser(description="Highlight lines matching specific regex patterns with specified colors.")
    parser.add_argument('-i', '--input', type=str, help="Input file (default: stdin)")
    parser.add_argument('-o', '--output', type=str, help="Output file (default: stdout)")
    parser.add_argument('--self-test', action='store_true', help="Run unit tests")
    parser.add_argument('--config-dir', type=str, default=CONFIG_DIR, help="Configuration directory (default: ~/.config/highlight_patterns)")
    parser.add_argument('--create-configs', action='store_true', help="Create example configuration files")
    parser.add_argument('--theme', type=str, help="Theme to use from the theme file (default: 'default')")
    parser.add_argument('--theme-file', type=str, help="Path to a specific theme file (overrides --theme)")
    args = parser.parse_args()

    if args.self_test:
        unittest.main(argv=[sys.argv[0]])
        sys.exit(0)

    config_dir = Path(args.config_dir)

    if args.create_configs:
        create_example_configs(config_dir)
        sys.exit(0)

    theme_file_path = config_dir / "theme.json"
    if args.theme_file:
        theme_file_path = Path(args.theme_file)

    if not theme_file_path.is_file():
        logging.error(f"Theme file does not exist: {theme_file_path}. Run with --create-configs to create example configuration files.")
        sys.exit(1)

    themes = load_themes(theme_file_path)
    theme_name = args.theme if args.theme else 'default'

    if theme_name not in themes:
        logging.error(f"Theme '{theme_name}' not found in theme file.")
        sys.exit(1)

    selected_theme = themes[theme_name]
    reset_color = selected_theme.get('reset', "\033[0m")
    patterns = load_patterns(config_dir, selected_theme)

    if not patterns:
        logging.error(f"No pattern files found in {config_dir}. Run with --create-configs to create example configuration files.")
        sys.exit(1)

    # If no input file is provided and stdin is a terminal, show the help message
    if not args.input and sys.stdin.isatty():
        parser.print_help()
        sys.exit(0)

    input_stream = sys.stdin
    if args.input:
        input_path = Path(args.input)
        if not input_path.is_file():
            logging.error(f"Input file does not exist: {args.input}")
            sys.exit(1)
        input_stream = input_path.open('r')

    output_stream = sys.stdout
    if args.output:
        output_path = Path(args.output)
        try:
            output_stream = output_path.open('w')
        except Exception as e:
            logging.error(f"Error opening output file: {args.output}. Error: {e}")
            sys.exit(1)

    try:
        process_input(input_stream, output_stream, patterns, reset_color)
    except Exception as e:
        logging.error(f"An error occurred during processing: {e}")
        sys.exit(1)
    finally:
        if args.input:
            input_stream.close()
        if args.output:
            output_stream.close()

    sys.exit(0)

class TestHighlightPatterns(unittest.TestCase):
    """
    Unit tests for the highlight_patterns script.
    """
    def test_highlight_line(self):
        themes = {
            "red": "\033[1;37;41m",
            "green": "\033[37;42m",
            "reset": "\033[0m"
        }
        patterns = [
            (re.compile(r"\b0% packet loss\b"), themes["green"]),
            (re.compile(r"\b\d+% packet loss\b"), themes["red"])
        ]
        line = "100% packet loss"
        expected = f"{themes['red']}100% packet loss{themes['reset']}"
        self.assertEqual(highlight_line(line, patterns, themes["reset"]), expected)

    def test_no_highlight(self):
        themes = {
            "red": "\033[1;37;41m",
            "green": "\033[37;42m",
            "reset": "\033[0m"
        }
        patterns = [
            (re.compile(r"\b0% packet loss\b"), themes["green"]),
            (re.compile(r"\b\d+% packet loss\b"), themes["red"])
        ]
        line = "No loss"
        self.assertEqual(highlight_line(line, patterns, themes["reset"]), line)

    def test_another_pattern(self):
        themes = {
            "red": "\033[1;37;41m",
            "green": "\033[37;42m",
            "reset": "\033[0m"
        }
        patterns = [
            (re.compile(r"\b0% packet loss\b"), themes["green"]),
            (re.compile(r"\b\d+% packet loss\b"), themes["red"])
        ]
        line = "0% packet loss"
        expected = f"{themes['green']}0% packet loss{themes['reset']}"
        self.assertEqual(highlight_line(line, patterns, themes["reset"]), expected)

if __name__ == "__main__":
    main()
