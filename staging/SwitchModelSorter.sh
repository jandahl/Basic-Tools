#!/bin/bash

# Define default file names
all_ips_file="/home/netadm/switch-script/jobs/all"
chassis_dir="/home/netadm/switch-script/jobs/show_chassis/output"
old_ips_file="/tmp/old_ips"
new_ips_file="/tmp/new_ips"
output_file="/tmp/output"

# Define help function
function print_help {
  echo "Usage: $0 [-h] [-o] [-n] [-a all_ips_file] [-c chassis_dir] [-O old_ips_file] [-N new_ips_file] [-O output_file]"
  echo "  -h              Display this help message"
  echo "  -o              Output only old devices"
  echo "  -n              Output only new devices"
  echo "  -a all_ips_file Path to all_ips file (default: $all_ips_file)"
  echo "  -c chassis_dir  Path to CHASSIS directory (default: $chassis_dir)"
  echo "  -O old_ips_file Path to output file for old devices (default: $old_ips_file)"
  echo "  -N new_ips_file Path to output file for new devices (default: $new_ips_file)"
  echo "  -O output_file  Path to output file for full data (default: $output_file)"
  exit 0
}

# Parse command line options
while getopts ":ho:n:a:c:O:N:O:" opt; do
  case ${opt} in
    h )
      print_help
      ;;
    o )
      output_old=true
      ;;
    n )
      output_new=true
      ;;
    a )
      all_ips_file=$OPTARG
      ;;
    c )
      chassis_dir=$OPTARG
      ;;
    O )
      old_ips_file=$OPTARG
      ;;
    N )
      new_ips_file=$OPTARG
      ;;
    O )
      output_file=$OPTARG
      ;;
    \? )
      echo "Invalid option: -$OPTARG" 1>&2
      print_help
      ;;
    : )
      echo "Option -$OPTARG requires an argument." 1>&2
      print_help
      ;;
  esac
done

shift $((OPTIND -1))

# Check if either -o or -n options were specified
if [[ $output_old && $output_new ]]; then
  echo "Error: Cannot output both old and new devices" 1>&2
  print_help
fi

# Read all_ips file into array
readarray -t all_ips < "$all_ips_file"

# Loop over array and lookup model for each IP
for ip in "${all_ips[@]}"; do
  # Remove trailing newline
  ip=${ip%$'
'}

  # Check if IP is valid
  if ! [[ $ip =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Error: Invalid IP address: $ip" 1>&2
    continue
  fi

  # Lookup chassis file for IP
  chassis_file="$chassis_dir/$ip"
  if ! [[ -f $chassis_file ]]; then
    echo -e "$ip	-	No model" >> "$output_file"
    continue
  fi

  # Search for model information in chassis file
  model=$(grep -m 1 -oP 'Model Name:\s*\K(OS)?(6450|6600|6800|6850|6850E|6860|6900)' "$chassis_file")
  if [[ -z $model ]]; then
    echo -e "$ip	$(host "$ip" | awk '{print $NF}')	No model" >> "$output_file"
    continue
  fi

  # Classify model as old or new
  if [[ $model =~ ^(OS)?(6450|6600|6800|6850|6850E)$ ]]; then
    classification="old"
  else
    classification="new"
  fi

  # Output to appropriate file(s)
  if [[ $output_old && $classification == "old" ]]; then
    echo "$ip" >> "$old_ips_file"
  elif [[ $output_new && $classification == "new" ]]; then
    echo "$ip" >> "$new_ips_file"
  else
    echo -e "$ip	$(host "$ip" | awk '{print $NF}')	$model" >> "$output_file"
  fi
done

# Output full data if neither -o nor -n options were specified
if ! [[ $output_old || $output_new ]]; then
  cat "$output_file"
fi
