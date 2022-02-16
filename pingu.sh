#!/usr/bin/env bash

function aboutMe() {
    printf "\n\t%s, ver %s" "${scriptName}" "${scriptVersion}"
    printf "\nPing a given host with a certain frequency - 5 seconds default - and save in a time stamped file"
    printf "\nUsage:\n\n\t%s%s ADDRESS %s" "${scriptFile}" "${Emphasize}" "${ColorOff}"
    printf "\n\n\tExample:"
    printf "\n\t\t%s%s www.example.org 10%s" "${scriptFile}" "${Emphasize}" "${ColorOff}"
    printf "\n\n\tSet timer to 10 seconds:"
    printf "\n\t\t%s%s -t 10 %s www.example.org\n\n" "${scriptFile}" "${Emphasize}" "${ColorOff}"
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
echo


function main() {
	shitInit
	[ -d ~/Pinglog ] || mkdir ~/Pinglog
	file=~/Pinglog/$(date +%Y-%m-%d-kl-%H-%M).pinglog.${testItem}.txt
	touch ${file}

	echo -e "Pinging ${testItem} every "${sleepTimer}" seconds - started $(date +%Y-%m-%d\ at\ %H\:%M)\n\nTime stamped results saved in "${file}" "${ColorOff}" "
	
    while sleep "${sleepTimer}"
	do
	        if $(ping -c 1 "${testItem}" 1> /dev/null 2>&1); then
	        	printf "${allOK}"
	        	savestring="$(date +%Y-%m-%d\ %H:%M:%S) - ${testItem} - ${pingoutput} ms"
	        else
	        	printf "${oShit}"
	        	savestring="$(date +%Y-%m-%d\ %H:%M:%S) - ${testItem} - No reply"
	        fi
	        echo ${savestring} >> ${file}
	done
}

shitInit() {
	# Just comment out the versions you don't want
	# Note that not all VTYs handle double wide emojis equally well so I've added a space to accomodate. YMMV.
    # allOK="."
    # oShit="!"
    # allOK="✅ "
    # oShit="⛔️ "
    allOK="👌 "
    oShit="💩 "
    # clownWorld="🤡"
}

defaultTitle=${HOSTNAME}
scriptFile=$(basename "${0}")
scriptName="pingu"
scriptVersion="2021-10-12 JGM"
sleepTimer="5"
isotime="$(date +"%Y-%m-%dT%H:%M:%SZ")"

colorInit

## Fjernet fordi jeg ikke gider at fjerne OPTARGs fra $*
while getopts ":t:" opt; do
    case $opt in
        t)
            echo -e "\n-r was triggered, so I shall retry every $OPTARG seconds" >&2
            export sleepTimer="${OPTARG}"
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
testItem="${1}"

if [ "$#" -lt 1 ]; then
    clear
    aboutMe
    exit
else
    clear
    main
fi
