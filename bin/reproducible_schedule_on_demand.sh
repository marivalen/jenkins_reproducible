#!/bin/bash

# Copyright 2014 Holger Levsen <holger@layer-acht.org>
#         © 2015 Mattia Rizzolo <mattia@mapreri.org>
# released under the GPLv=2

DEBUG=false
. /srv/jenkins/bin/common-functions.sh
common_init "$@"

# common code defining db access
. /srv/jenkins/bin/reproducible_common.sh

schedule_packages() {
	# these packages are manually scheduled, so should have high priority,
	# so schedule them in the past, so they are picked earlier :)
	DATE="2014-10-01 00:23"
	TMPFILE=$(mktemp)
	for PKG in $PACKAGES ; do
		echo "REPLACE INTO schedule (package_id, date_scheduled, date_build_started) VALUES ('$PKG', '$DATE', '');" >> $TMPFILE
	done
	cat $TMPFILE | sqlite3 -init $INIT ${PACKAGES_DB}
	rm $TMPFILE
}

check_candidates() {
	PACKAGES=""
	PACKAGES_NAMES=""
	TOTAL=0
	for PKG in $CANDIDATES ; do
		RESULT=$(sqlite3 -init $INIT ${PACKAGES_DB} "SELECT id, name from sources WHERE name='$PKG' AND suite='$SUITE';")
		if [ ! -z "$RESULT" ] ; then
			PACKAGES="$PACKAGES $(echo $RESULT|cut -d '|' -f 1)"
			PACKAGES_NAMES="$PACKAGES_NAMES $(echo $RESULT|cut -d '|' -f 2)"
			let "TOTAL+=1"
		fi
	done
	case $TOTAL in
	0)
		echo "No packages to schedule, exiting."
		exit 0
		;;
	1)
		PACKAGES_TXT="package"
		;;
	*)
		PACKAGES_TXT="packages"
		;;
	esac
}

#
# main
#
set +x
SUITE="$1"
shift
CANDIDATES="$@"
check_candidates
if [ ${#PACKAGES} -gt 256 ] ; then
	BLABLABLA="..."
fi
PACKAGES=$(echo $PACKAGES)
ACTION="manually rescheduled"
if [ -n "${BUILD_URL:-}" ] ; then
	ACTION="rescheduled by $BUILD_URL"
fi
MESSAGE="$TOTAL $PACKAGES_TXT $ACTION for $SUITE: ${PACKAGES_NAMES:0:256}$BLABLABLA"

# finally
schedule_packages
cd /srv/jenkins/bin
python3 -c "from reproducible_html_indexes import build_page; build_page('scheduled')"
echo
echo "$MESSAGE"
if [ -z "${BUILD_URL:-}" ] ; then
	kgb-client --conf /srv/jenkins/kgb/debian-reproducible.conf --relay-msg "$MESSAGE"
fi
echo "============================================================================="
echo "The following $TOTAL source $PACKAGES_TXT $ACTION for $SUITE: $PACKAGES_NAMES"
echo "============================================================================="
echo
