#!/usr/bin/env bash

function aboutMe() {
    clear
    printf "\n\t%s, version %s" "${scriptName}" "${scriptVersion}"
    printf "\n\nWait for IP to respond to ping, then do COMMAND"
    printf "\n\nUsage:"
    printf "\n\t%s%s COMMAND IP%s" "${Emphasize}" "${scriptFile}" "${ColorOff}"
    printf "\nExample:"
    printf "\n\t%s%s%s telnet 10.20.30.40%s" "${Emphasize}" "${scriptFile}" "${ColorOff}" "${ColorOff}"
    printf "\n\t%s%s%s ssh router-name%s\n\n" "${Emphasize}" "${scriptFile}" "${ColorOff}" "${ColorOff}"
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

shitInit() {

    allOK="👌"
    oShit="."
    clownWorld="🤡"
    pingFlags="-c 1 -W 1"
    dateFlags="+"%Y-%m-%dT%H:%M:%SZ""

    if [ -n "$STY" ] || [ -n "$TMUX" ]; then
        trap 'echo -n -e "\033k${defaultTitle}\033\\"' 0 1 2 15
        echo -n -e "\033k${scriptName}\033\\"
    fi

    # OS specific differences 🤦‍♂️
    if [[ $OSTYPE == "linux-gnu"* ]]; then
        true
    elif [[ $OSTYPE == "darwin"* ]]; then
        true
    elif [[ $OSTYPE == "cygwin" ]]; then
        # POSIX compatibility layer and Linux environment emulation for Windows
        allOK="✅"
        oShit="⛔️"
        clownWorld="⛈ "
    elif [[ $OSTYPE == "msys" ]]; then
        true
    elif [[ $OSTYPE == "win32" ]]; then
        true
    elif [[ $OSTYPE == "freebsd"* ]]; then
        true
    else
        true
    fi
}

function icmpBlast() {
    ## Ping section
    # for icmpechoes in $(seq 1 "${numPings}"); do
    #     ping -t 1 -c 1 "${testItem}" 1> /dev/null 2>&1 && printf "${allOK}" || printf "${oShit}"
    # done

    if [ ! $(ping ${pingFlags} "${targetIP}" > /dev/null) ]; then
        downDate="$(date ${dateFlags})"
        printf "Invoked %s%s%s" "${Emphasize}" "${downDate}" "${ColorOff}"
        echo -e "\033kping $targetIP\033\\"
        printf "\nWaiting for %s%s%s to come up." "${Emphasize}" "${targetIP}" "${ColorOff}"
        until ping ${pingFlags} "${targetIP}" > /dev/null; do
            printf "%s" "${oShit}"
            sleep 4
        done
        upDate="$(date ${dateFlags})"
        printf "\n%s%s%s came up at %s%s%s!\n" "${Emphasize}" "${targetIP}" "${ColorOff}" "${Emphasize}" "${upDate}" "${ColorOff}"
    fi

}

function main() {
    icmpBlast
}

colorInit

# defaultTitle=${HOSTNAME}
scriptFile=$(basename "${0}")
scriptName="up-yours"
scriptVersion="2020-09-08 JGM"
defaultTitle="up-yours"
targetIP="${@: -1}"

if [ "$#" -lt 1 ]; then
    aboutMe
    exit
else
    shitInit
    main
    $*
fi
