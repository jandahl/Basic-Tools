#!/usr/bin/env bash

function aboutMe() {
    printf "\n\t%s, version %s" "${scriptName}" "${scriptVersion}"
    printf "\n\tDumb as shit script that takes as an argument a subdirectory of ${baseDirectory}"
    printf "\n\tIt will then list files in that directory, use the file names as HOSTNAMES"
    printf "\n\tIt will then direct %s clogin %s to trawl through the HOSTNAMES and" "${Emphasize}" "${ColorOff}"
    printf "\n\tfeed the commands in the so named file to the device"

    printf "\n\n\tExample"
    printf "\n\n\t%s %s move-traffic-away-from-data1 %s" "${scriptFile}" "${Emphasize}" "${ColorOff}"
    printf "\n\n\t%s %s move-traffic-back-to-data1 %s" "${scriptFile}" "${Emphasize}" "${ColorOff}"
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

function init() {

    # configDirectory="/home/a-edbafjgm/FLYT-DATACENTERTRAFIK/FRA-DATA1/"
    configDirectory="${baseDirectory}/${ottomationSource}"
    configFileList="${configDirectory}/*"
    # fjern risiko for at fejle pga. tomme kataloger
    shopt -s nullglob
}

function main() {
    for configFile in ${configFileList}; do
        device=$(echo "${configFile}" | awk -F"/" '{ print $NF }')
        echo "Using ${configFile} on ${device}!"
        # clogin -x "${configFile}" "${device}"
    done
    echo "Went through all devices!"
}

# defaultTitle=${HOSTNAME}
scriptFile=$(basename "${0}")
scriptName="ottomator"
scriptVersion="2020-09-07 JGM"
baseDirectory="/home/a-edbafjgm/otto"

if [ "$#" -lt 1 ]; then
    aboutMe
    exit
else
    configDirectory="${baseDirectory}/${1}"
    if [ -d "$configDirectory" ]; then
        export ottomationSource="${1}"
        # clear
        init
        main
    else
        printf "\n\n\t%sERROR!%s" "${Emphasize}" "${ColorOff}"
        printf "\n\tCan't find %s inside %s" "${1}" "${baseDirectory}"
        printf "\n\tAvailabe directories:"
        for directory in "${baseDirectory}"/*; do
            printf '%s\n' "${directory}"
        done
    fi
fi
