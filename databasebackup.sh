#!/bin/bash
function init() {
	# Backup storage directory 
	backupfolder="/home/jgm/backups"
	mkdir -p "$backupfolder"
	# Notification email address 
	recipient_email="jgm@forcetechnology.com"
	# MySQL user
	user="wiki"
	# MySQL password
	password=$(cat /home/jgm/bin/wiki/adgangskode)
	# Number of days to store the backup 
	keep_day="180"

	backuptime="$(date +%d-%m-%Y_%H-%M-%S)"
	sqlfile="${backupfolder}/all-database-${backuptime}.sql"
	zipfile="${backupfolder}/all-database-${backuptime}.zip"
}

function main() {
	# todo: add "lock database before backup and unlcok after"
	makebackup
	compressbackup
	deleteoldbackups
}

function makebackup() {
	# Create a backup 
	if mysqldump -u "${user}" -p"${password}" --all-databases > "${sqlfile}"; then
	  echo 'Sql dump created' 
	else
	  echo 'mysqldump return non-zero code' | mailx -s 'No backup was created!' "${recipient_email}"  
	  exit 
	fi 
}

function compressbackup() {
	# Compress backup 
	if zip "${zipfile}" "${sqlfile}"; then
	  echo 'The backup was successfully compressed' 
	else
	  echo 'Error compressing backup' | mailx -s 'Backup was not created!' "${recipient_email}" 
	  exit 
	fi 
	rm "${sqlfile}"
	echo "${zipfile}" | mailx -s 'Backup was successfully created' "${recipient_email}" 
}

function deleteoldbackups() {
	# Delete old backups 
	find "${backupfolder}" -mtime +"${keep_day}" -delete
}

init
main
