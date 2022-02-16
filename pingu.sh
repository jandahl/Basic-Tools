#!/usr/bin/env bash

scriptFile=$(basename "${0}")
scriptName="pingu"
scriptVersion="2022-02-16 JGM"
sleepTimer="5"
outputDirectory="$HOME/Pinglog"
isotime="$(date +"%Y-%m-%dT%H:%M:%SZ")"

function aboutMe() {
    printf "\n\t%s, ver %s" "${scriptName}" "${scriptVersion}"
    printf "\nPing a given host with a certain frequency - %s seconds default - and save in a time stamped file" "${sleepTimer}"
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

function meatAndPotatoes() {
        if $(eval ping -c 1 "${testItem}" 1> /dev/null 2>&1); then
            printf "${allOK}"
            savestring="$(date +%Y-%m-%d\ %H:%M:%S) - ${testItem} - ${pingoutput} ms"
        else
            printf "${oShit}"
            savestring="$(date +%Y-%m-%d\ %H:%M:%S) - ${testItem} - No reply"
        fi
        echo ${savestring} >> ${file}
}

function main() {
	shitInit
	[ -d "$outputDirectory" ] || mkdir "$outputDirectory"
	file=${outputDirectory}/$(date +%Y-%m-%d-kl-%H-%M).pinglog.${testItem}.txt
	touch "${file}"

	echo -e "Pinging ${testItem} every ${sleepTimer} seconds - started ${isotime} \n"
    echo -e "Time stamped results saved in ${file} ${ColorOff}"
	
    while sleep "${sleepTimer}"
	do
        meatAndPotatoes
	done
}

shitInit() {
	# Just comment out the versions you don't want
	# Note that not all VTYs handle double wide emojis equally well so I've added a space to accomodate. YMMV.
    allOK="."
    oShit="!"
    # allOK="✅ "
    # oShit="⛔️ "
    # allOK="👌 "
    # oShit="💩 "
    # clownWorld="🤡"
}


colorInit

## Fjernet fordi jeg ikke gider at fjerne OPTARGs fra $*
while getopts ":t:" opt; do
    case $opt in
        t)
            echo -e "\n-t was triggered, so I shall retry every $OPTARG seconds" >&2
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
