#!/usr/bin/env bash

function aboutMe() {
    printf "\n\t%s, ver %s" "${scriptName}" "${scriptVersion}"
    printf "\n\tTries to acces the supplied IP or FQDN via several methods."
    printf "\n\tDoesn't care about IPv6."
    printf "\n\n\tExample:"
    printf "\n\t\t%s %s example.com%s" "${scriptFile}" "${Emphasize}" "${ColorOff}"
    printf "\n\t\t%s %s example.com example.org%s" "${scriptFile}" "${Emphasize}" "${ColorOff}"
    printf "\n\n\tAlso has a built-in retry timer, using -r! (Note: only way to get out is killing the terminal)"
    printf "\n\t\t%s %s-r SECONDS example.com%s" "${scriptFile}" "${Emphasize}" "${ColorOff}"
    printf "\n\n\tExample:"
    printf "\n\t\t%s %s-r 20 example.com example.org%s" "${scriptFile}" "${Emphasize}" "${ColorOff}"
    printf "\n\n\tWant to add ONE custom port to the curl tests? Use -p!"
    printf "\n\t\t%s %s-p PORT example.com%s" "${scriptFile}" "${Emphasize}" "${ColorOff}"
    printf "\n\n\tExample:"
    printf "\n\t\t%s %s-p 666 example.com example.org%s" "${scriptFile}" "${Emphasize}" "${ColorOff}"
}

function colorInit() {
    ColorOff=$'\e[0m'  # Text Reset
    BWhite=$'\e[1;37m' # Bold White
    BRed=$'\e[1;31m'   # Bold Red
    LGray=$'\e[0;37m'  # Light Gray

    if [ -z "$Diminish" ]; then
        Diminish=${LGray}
    fi
    if [ -z "$Emphasize" ]; then
        Emphasize=${BRed}
    fi
}

function icmpBlast() {
    ## Ping section
    printf "\n\t%s pings: " "${numPings}"
    for icmpechoes in $(seq 1 "${numPings}"); do
        ping -t 1 -c 1 "${testItem}" 1> /dev/null 2>&1 && printf "%s" "${allOK}" || printf "%s" "${oShit}"
    done
}

function curlUnsafe() {
    printf "\n\tTrying to curl port 80 (HTTP)... "
    testURL="http://${testItem}"
    actualCurling
}

function curlSafe() {
    printf "\n\tTrying to curl port 443 (HTTPS)... "
    testURL="https://${testItem}"
    actualCurling
}

function actualCurling() {
    curl ${curlFlags} "${testURL}" 1> /dev/null 2>&1 && printf "${allOK}" || printf "${oShit}"
}

function netcat() {
    printf "\n\tTrying to netcat..."
    for portNumber in ${curlPorts}; do
        actualNetcatting
    done
}

function actualNetcatting() {
    printf "\n\t\tport %s... " "${portNumber}"
    nc ${netcatFlags} "${testItem}" "${portNumber}" 1> /dev/null 2>&1 && printf "${allOK}" || printf "${oShit}"
}

function reverseAndForwardLookup() {
    # echo $testItem
    if [[ ${testItem} =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
        # echo "Input looks like an IPv4! Let's try for Reverse DNS! "
        reverseLookup=$(echo $(host -4 -t PTR "${testItem}" "${nameServer}" | grep ${testItem} | awk '{print $NF}'))
        if [ "${reverseLookup}" == "3(NXDOMAIN)" ]; then
            digOutput="No PTR/Reverse DNS! ${clownWorld}"
        else
            digOutput="${reverseLookup}"
        fi

    else
        # echo "Input does not look like an IPv4! Let's try for an A record!"
        digOutput=$(echo $(host -4 -t A "${testItem}" "${nameServer}" | grep ${testItem} | awk '{print $NF}'))
    fi

}

shitInit() {
    numPings="4"

    curlPorts="22 80 443 3389"
    if [ -z "$additionalPort" ]; then
        true
    else
        curlPorts="${curlPorts} ${additionalPort}"
    fi
    curlFlags="--insecure --connect-timeout 1"

    netcatFlags="-w 1 -z"

    allOK="👌"
    oShit="💩"
    clownWorld="🤡"

    if [ -n "$STY" ] || [ -n "$TMUX" ]; then
        trap 'echo -n -e "\033k${defaultTitle}\033\\"' 0 1 2 15
        echo -n -e "\033k${scriptName}\033\\"
    fi

    # OS specific differences 🤦‍♂️
    if [[ $OSTYPE == "linux-gnu"* ]]; then
        true
    elif [[ $OSTYPE == "darwin"* ]]; then
        # Mac OSX
        netcatFlags="-G 1 -z"
    elif [[ $OSTYPE == "cygwin" ]]; then
        # POSIX compatibility layer and Linux environment emulation for Windows
        allOK="✅"
        oShit="⛔️"
        clownWorld="⛈ "
    elif [[ $OSTYPE == "msys" ]]; then
        # Lightweight shell and GNU utilities compiled for Windows (part of MinGW)
        echo "o shit it's windows msys, haven't tested this but let's try"
    elif [[ $OSTYPE == "win32" ]]; then
        # I'm not sure this can happen.
        echo "o shit it's win32, haven't tested this but let's try"
    elif [[ $OSTYPE == "freebsd"* ]]; then
        # ...
        echo "o shit it's freebsd, haven't tested this but let's try"
    else
        true
    fi
}

function letsGetReadyToRumble() {
    for testItem in ${testVictimList}; do
        reverseAndForwardLookup
        printf "\nConcerning %s%s%s (%s%s%s) - %s" "${Emphasize}" "${testItem}" "${ColorOff}" "${Emphasize}" "${digOutput}" "${ColorOff}" "${isotime}"
        icmpBlast
        curlUnsafe
        curlSafe
        netcat
        printf "\n"
    done
}

# function trap_ctrlc() {
#     # perform cleanup here
#     echo"Ctrl-C caught...performing clean up"
#     echo"Doing cleanup"
#     # exit shell script with error code 2
#     # if omitted, shell script will continue execution
#     exit2
# }
# # initialise trap to call trap_ctrlc function
# # when signal 2 (SIGINT) is received
# trap"trap_ctrlc"2

function main() {
    shitInit
    if [ "$sleepTimer" -gt 0 ]; then
        # printf "Sleep Timer has been set! Will rerun every %s%s%s seconds!" "${Emphasize}" "${sleepTimer}" "${ColorOff}"
        while true; do
            clear
            letsGetReadyToRumble
            for ((countDown = sleepTimer; countDown > 0; countDown--)); do
                tput cup 10 $l
                # echo -n "Waiting ${Emphasize}${i}${ColorOff} seconds and doing it all again!"
                printf "\n\n\t\t\tWaiting %s%s%s seconds and doing it all again!" "${Emphasize}" "${countDown}" "${ColorOff}"
                sleep 1
            done
        done
    else
        letsGetReadyToRumble
    fi
}

defaultTitle=${HOSTNAME}
scriptFile=$(basename "${0}")
scriptName="multitester"
scriptVersion="2020-09-08 JGM"
sleepTimer="0"
isotime="$(date +"%Y-%m-%dT%H:%M:%SZ")"

# Well, sometimes the system differentiates between the "real"
# DNS server from DHCP, and the one used in a VPN tunnel.
# Therefore I am forced to make a var for this stupid shit.
nameServer="10.2.1.10"

colorInit

## Fjernet fordi jeg ikke gider at fjerne OPTARGs fra $*
while getopts ":r:p:" opt; do
    case $opt in
        r)
            echo -e "\n-r was triggered, so I shall retry every $OPTARG seconds" >&2
            export sleepTimer="${OPTARG}"
            ;;
        p)
            printf "\n-p was triggered, adding port %s to the mix!" "${OPTARG}"
            export additionalPort="${OPTARG}"
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            exit 1
            ;;
        :)
            echo "Option -$OPTARG requires an argument." >&2
            exit 1
            ;;
    esac
done
shift $((OPTIND - 1))
testVictimList="${*}"

if [ "$#" -lt 1 ]; then
    clear
    aboutMe
    exit
else
    clear
    main
fi
