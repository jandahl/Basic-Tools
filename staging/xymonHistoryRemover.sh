#!/usr/bin/env bash

### Staging functions
function aboutMe() {
    printf "\n\t%s, ver %s" "${scriptName}" "${scriptVersion}"
    printf "\n\tDelete monitoring history from xymon"
    printf "\n\tSupply one or more host names as provided in the first column of %s" "${xymonConfigFile}"
    printf "\n\n\t%sImportant!%s Will NOT delete the relevant entries in the configuration file." "${Emphasize}" "${ColorOff}"
    printf "\n\n\t%sImportant!%s You should delete those first manually." "${Emphasize}" "${ColorOff}"
    printf "\n\n\tExample:"
    printf "\n\t\t%s %s example.com%s" "${scriptFile}" "${Emphasize}" "${ColorOff}"
    printf "\n\t\t%s %s example.com example.org%s" "${scriptFile}" "${Emphasize}" "${ColorOff}"
    printf "\n\n\n"
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

function goDeleteHistory() {
	for removableItem in ${itemsToRemoveFromXymon}; do
		echo "Her slettes ikke endnu dette er bare et testscript indtil videre"
		# /home/xymon/server/bin/xymon 127.0.0.1 "drop ${removableItem}"
        printf "--------"
		printf "Asked xymon to delete history for %s - remember that if 'hosts.cfg' still points\nto the device, it'll just pop up again." "${removableItem}"
		grep "${removableItem}" ${xymonConfigFile}
	done
}

function askIfUserIsSure() {
	printf "You have stated that you want to remove the following item(s);\n\t%s" "${itemsToRemoveFromXymon}"
	read -p "Do you want to proceed? [y/N] " yn

	case $yn in 
    	[Yy]*) echo "OK, we will proceed"; return 0;;
    	[Nn]*) echo "Aborted"; return 1;;
    	*    ) echo "Invalid response, aborting"; exit 1;;
    esac
}

function main() {
    askIfUserIsSure
    goDeleteHistory
}

### Let's roll! 
## vars
itemsToRemoveFromXymon="${*}"
scriptFile=$(basename "${0}")
scriptName="xymon-remover"
scriptVersion="2022-08-23 JGM"
isotime="$(date +"%Y-%m-%dT%H:%M:%SZ")"
xymonConfigFile="/home/xymon/server/etc/hosts.cfg"
## colors
colorInit

if [ "$#" -lt 1 ]; then
    aboutMe
    exit
else
    main
fi