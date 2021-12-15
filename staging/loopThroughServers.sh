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
}; colorInit

function initialize {
  outputdir="/home/jgm/log4j"
  mkdir -p ${outputdir}
  serverList="lbrb01 lbrb02 lbrb03 lbrb04 lbrb05 lbrb06 lbrb07 lbrb09 lbrb10 lbrb11 lbrb12 lbrb13 lbrb14 lbrb15 lbrb16"
  commandSet="locate -i log4j; exit"
}; initialize


function main {
  for server in ${serverList}; do
    echo "Trying ${server}; assuming ${Emphasize}updatedb${ColorOff} has been run"
    ssh ${server} "${commandSet}" > ${outputdir}/$(date +%Y-%m-%d)-${server}.txt
  done
}; main
