#!/bin/bash
. /.denv
while getopts  p: flag
do
    case "${flag}" in
        p) push=${OPTARG};;
    esac
done
export GIT_SSH_COMMAND="ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no"
cd /etc/dn42ap_py
./DN42AP_regenerate_config.py
if [ -z ${push+x} ]; then 
	echo "puash is unset"; 
else 
	echo "push is set to '$push'"; 
	cd /git_sync_root
	git pull
	git add -A
	git commit -m "${NODE_NAME} update ap_regen"
	git push
fi
