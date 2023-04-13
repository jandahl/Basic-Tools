#!/bin/bash


### ChatGPT 3.5 prompt:
# I would like a bash script that has a multidimensional array with PORT NUMBER and PORT USAGE, e.g. "80","http";"443","https". The script should expect a target host or IPv4 address as a command line argument and give a help screen if it does not receive one. If it receives a valid command line argument, it should then proceed to: 1) Output the target on screen and do a DNS A lookup/reverse PTR lookup and print this in a parenthesis. 2) Try to reach the given target using cURL, given a separate multidimensional array. 3) For each member of its multidimensional array it should try to reach it via netcat. The script should accept several hostnames and/or IPs. Also, I should like to be able to serve this script command line arguments that add port numbers to either cURL (e.g. "-c 123,456" or "--curl 123,456") or netcat (e.g. "-p 789,123" or "--ports 789,123"), and an option for a retry timer in seconds (e.g. "-r 10" or "--retry 10"). 

# Define the arrays
CURL_PORTS=("80:http" "443:https")
NC_PORTS=("22:ssh" "80:http" "443:https")

# Define message variables
TARGET_RESOLVING_MSG="Resolving target..."
TARGET_RESOLVED_MSG="Target resolved: "
CURL_CHECK_MSG="Trying cURL on "
CHECK_SUCCESS_MSG="Success!"
CHECK_FAILURE_MSG="Failed."
NC_CHECK_MSG="Trying netcat on "

# Define functions
function usage {
  echo "Usage: $0 [-c|--curl PORTS] [-p|--ports PORTS] [-r|--retry SECONDS] TARGET..."
  exit 1
}

function resolve {
  local target="$1"
  echo -n "$TARGET_RESOLVING_MSG"
  local ip=$(dig +short "$target" | tail -1)
  echo "$TARGET_RESOLVED_MSG $target (${ip:-unknown})"
}

function curl_check {
  local target="$1"
  local ports="$2"
  for element in "${CURL_PORTS[@]}"; do
    local port=${element%%:*}
    local proto=${element#*:}
    if [[ "$ports" == *"$port"* ]]; then
      local url="$proto://$target/"
      echo -n "$CURL_CHECK_MSG$port... "
      curl -I -m 5 "$url" >/dev/null 2>&1 && echo "$CHECK_SUCCESS_MSG" || echo "$CHECK_FAILURE_MSG"
    fi
  done
}

function nc_check {
  local target="$1"
  local ports="$2"
  for element in "${NC_PORTS[@]}"; do
    local port=${element%%:*}
    local service=${element#*:}
    if [[ "$ports" == *"$port"* ]]; then
      echo -n "$NC_CHECK_MSG$target:$port (${service})... "
      nc -w 1 -z "$target" "$port" >/dev/null 2>&1 && echo "$CHECK_SUCCESS_MSG" || echo "$CHECK_FAILURE_MSG"
    fi
  done
}

# Parse command line arguments
curl_ports=""
nc_ports=""
retry=""
targets=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    -c|--curl)
      curl_ports="$2"
      shift 2
      ;;
    -p|--ports)
      nc_ports="$2"
      shift 2
      ;;
    -r|--retry)
      retry="$2"
      shift 2
      ;;
    -*)
      usage
      ;;
    *)
      targets="$targets $1"
      shift
      ;;
  esac
done

# Check if targets were specified
if [ -z "$targets" ]; then
  usage
fi

# Loop through targets
for target in $targets; do
  echo "Testing $target..."
  resolve "$target"
  curl_check "$target" "${curl_ports:-80,443}"
  nc_check "$target" "${nc_ports:-22,80,443}"
done
