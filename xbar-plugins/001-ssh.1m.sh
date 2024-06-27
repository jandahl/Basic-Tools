#!/bin/zsh
#
# SSH utility for quickly accessing configured hosts from ~/.ssh/config
#
# <xbar.title>SSH</xbar.title>
# <xbar.version>v1.2</xbar.version>
# <xbar.author>Jan Gronemann</xbar.author>
# <xbar.author.github>YourGitHubUsername</xbar.author.github>
# <xbar.desc>Quickly SSH to your favorite hosts listed in your ~/.ssh/config file with status indicators.</xbar.desc>
#
# This script retrieves hostnames and IP addresses from ~/.ssh/config, checks SSH connectivity,
# and displays them in xbar with color-coded indicators (green for success, red for failure).
# It supports parallel processing for efficient connectivity checks and sorts the output alphabetically.
#
# Credits to the original concept by Thameera Senanayaka (github:thameera), enhanced and maintained by Jan Gronemann.
#
# For optimal performance, ensure ~/.ssh/config is correctly formatted with Host and HostName entries.
#

# Define colors and icons
typeset -A colors
colors=(
    "red"    "Crimson"
    "green"  "MediumSpringGreen"
)

typeset -A icons
icons=(
    "red"    "✧"
    "green"  "✦"
)

# Array of hosts to ignore
ignored_hosts=("host_to_ignore1" "host_to_ignore2")

# Function to check if a host is in the ignored list
is_ignored() {
    local host=$1
    for ignored_host in "${ignored_hosts[@]}"; do
        if [[ "$host" == "$ignored_host" ]]; then
            return 0  # Found in ignored_hosts
        fi
    done
    return 1  # Not found in ignored_hosts
}


# Function to check SSH connectivity for a host
check_ssh() {
    local host=$1
    local ip=${2:-""}

    if nc -z -G 1 "$ip" 22 > /dev/null 2>&1; then
        return 0  # Success
    else
        return 1  # Failure
    fi
}

# Loop through each host entry in ~/.ssh/config
typeset -A hosts
while read -r host; do
    # Get IP address and comments of the host from ~/.ssh/config
    hosts[$host]=""
    hosts["ip_$host"]="$(awk -v host="$host" '$1 == "Host" && $2 == host {found=1; next} found && /^$/ {exit} found && /^ *HostName / {print $2; exit}' ~/.ssh/config)"
    hosts["comment_$host"]="$(awk -v host="$host" '$1 == "Host" && $2 == host && $3 ~ /^#/ {print substr($0, index($0,$3))}' ~/.ssh/config)"

done < <(awk '/^Host / && !/\*/ {print $2}' ~/.ssh/config)

# Array to store formatted output lines
typeset -a output_lines

# Track if any SSH connections were successful
any_success=false

# Loop through each host entry in hosts array
for host in ${(k)hosts}; do
    # Check if the host should be ignored
    if is_ignored "$host"; then
        continue
    fi

    # Get IP address and comment
    ip="${hosts["ip_$host"]}"
    comment="${hosts["comment_$host"]}"

    # Proceed only if IP address is found
    if [[ -n "$ip" ]]; then
        # Prepare user-visible text
        user_text="$host"
        if [[ -n "$ip" ]]; then
            user_text+=" - $ip"
        fi

        # Check SSH port connectivity using nc (netcat) in parallel
        if check_ssh "$host" "$ip"; then
            actions="color=${colors[green]} bash=\"/usr/bin/open\" param1=\"-a\" param2=\"iterm\" param3=\"ssh://$host\""
            ping_status="${icons[green]}"
            any_success=true
        else
            actions="color=${colors[red]} bash=\"/usr/bin/open\" param1=\"-a\" param2=\"iterm\" param3=\"ssh://$host\""
            ping_status="${icons[red]}"
        fi

        # Format the line and add to output_lines array
        output_lines+=("$ping_status $user_text | $actions")
    fi
done

# Set the first output line conditionally
if $any_success; then
    echo "ssh"
else
    echo "🚫ssh"
fi
echo "---"

# Sort output_lines array
IFS=$'\n' sorted_output=($(sort <<<"${output_lines[*]}"))

# Print sorted output
for line in "${sorted_output[@]}"; do
    echo "$line"
done
