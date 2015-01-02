#!/bin/bash

# Copyright 2014-2015 Holger Levsen <holger@layer-acht.org>
# released under the GPLv=2

DEBUG=false
. /srv/jenkins/bin/common-functions.sh
common_init "$@"

cleanup_all() {
	sudo rm -rf --one-file-system $TMPDIR
}

TMPDIR=$(mktemp --tmpdir=/srv/live-build -d)
cd $TMPDIR
trap cleanup_all INT TERM EXIT

# $1 is used for the hostname and username
# $2 is choosing the flavor
lb config --distribution jessie --bootappend-live "boot=live config hostname=$1 username=$1"
case "$2" in
	standalone)	echo education-standalone > config/package-lists/live.list.chroot
			;;
	gnome)		echo gnome > config/package-lists/live.list.chroot
			;;
	xfce)		echo xfce4 > config/package-lists/live.list.chroot
			;;
	*)		;;
esac
sudo lb build
mkdir -p /srv/live-build/results
cp -v live-image-amd64.hybrid.iso /srv/live-build/results/$1_$2_live_amd64.iso

cleanup_all
trap - INT TERM EXIT
