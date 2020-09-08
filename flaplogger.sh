#!/usr/bin/env bash

scriptFile=$(basename "${0}")
scriptName="Uptime-and-downtime-logger"
scriptVersion="2016-08-26 JAGR"
defaultPingTimer=4
targetIP=${1}

if [ -z "${2}" ]; then
    pingTimer=${defaultPingTimer}
else
    pingTimer=${2}
fi

function aboutMe() {
    echo -e "\n\t${scriptName}, v ${scriptVersion}"
    echo -e "\n\tKeeps pinging every ${Emphasize}${pingTimer}${ColorOff} seconds with a timeout of 1 second"
    echo -e "\n\tTimer can be adjusted by a second argument (in seconds)."
    echo -e "\n\tExamples:"
    echo -e "\n\t${scriptFile}${Emphasize} dr.dk${ColorOff}"
    echo -e "\t${scriptFile} 10.20.30.40 ${Emphasize}30${ColorOff}\n"
}

function colorInit() {
    ColorOff=$'\e[0m'       # Text Reset
    BWhite=$'\e[1;37m'      # Bold White
    BRed=$'\e[1;31m'        # Bold Red
    upEmphasis=$'\e[1;35;42m'   # Bold Red
    LGray=$'\e[0;37m'       # Light Gray

    if [ -z "$Diminish" ]; then
        Diminish=${LGray};
    fi
    if [ -z "$Emphasize" ]; then
        Emphasize=${BRed};
    fi
}

function isUp() {
    # echo "isUp invoked"
    until ! ping -c 1 -W 1 "${targetIP}" > /dev/null
    do
            printf "."
            sleep ${pingTimer};
    done
    echo -e "\n${Emphasize}${targetIP}${ColorOff} went ${Emphasize}down${ColorOff} at ${Emphasize}$(date)${ColorOff}!"
    isDown
}

function isDown() {
    # echo "isDown invoked"
    until ping -c 1 -W 1 "${targetIP}" > /dev/null
    do
            printf "."
            sleep ${pingTimer};
    done
    echo -e "\n${upEmphasis}${targetIP}${ColorOff} came ${upEmphasis}up${ColorOff} at ${upEmphasis}$(date)${ColorOff}!"
    isUp    
}

function main() {
    echo "Invoked $(date). Pinging every ${pingTimer} seconds"
    if ping -c 1 -W 1 "${targetIP}" > /dev/null; then
        echo -e "\n${upEmphasis}${targetIP}${ColorOff} was ${upEmphasis}up${ColorOff} at ${upEmphasis}$(date)${ColorOff}!"
        isUp
    else
        echo -e "\n${Emphasize}${targetIP}${ColorOff} was ${Emphasize}down${ColorOff} at ${Emphasize}$(date)${ColorOff}!"
        isDown
    fi
}


colorInit

if [ "$#" -lt 1 ]; then
    aboutMe;
    exit
else
    main;
fi
