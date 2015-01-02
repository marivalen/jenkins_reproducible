#!/bin/bash

# Copyright 2014 Holger Levsen <holger@layer-acht.org>
# released under the GPLv=2

DEBUG=false
. /srv/jenkins/bin/common-functions.sh
common_init "$@"

# common code defining db access
. /srv/jenkins/bin/reproducible_common.sh

set +x
init_html
gather_stats

#
# create stats
#
# FIXME?: we only do stats up until yesterday... we also could do today too but not update the db yet...
DATE=$(date -d "1 day ago" '+%Y-%m-%d')
TABLE[0]=stats_pkg_state
TABLE[1]=stats_builds_per_day
TABLE[2]=stats_builds_age
TABLE[3]=stats_bugs
TABLE[4]=stats_notes
TABLE[5]=stats_issues
TABLE[6]=stats_meta_pkg_state
RESULT=$(sqlite3 -init ${INIT} ${PACKAGES_DB} "SELECT datum,suite from ${TABLE[0]} WHERE datum = \"$DATE\" AND suite = \"$SUITE\"")
if [ -z $RESULT ] ; then
	ALL=$(sqlite3 -init ${INIT} ${PACKAGES_DB} "SELECT count(name) from sources")
	GOOD=$(sqlite3 -init ${INIT} ${PACKAGES_DB} "SELECT count(status) from source_packages WHERE status = 'reproducible' AND date(build_date)<='$DATE';")
	GOOAY=$(sqlite3 -init ${INIT} ${PACKAGES_DB} "SELECT count(status) from source_packages WHERE status = 'reproducible' AND date(build_date)='$DATE';")
	BAD=$(sqlite3 -init ${INIT} ${PACKAGES_DB} "SELECT count(status) from source_packages WHERE status = 'unreproducible' AND date(build_date)<='$DATE';")
	BAAY=$(sqlite3 -init ${INIT} ${PACKAGES_DB} "SELECT count(status) from source_packages WHERE status = 'unreproducible' AND date(build_date)='$DATE';")
	UGLY=$(sqlite3 -init ${INIT} ${PACKAGES_DB} "SELECT count(status) from source_packages WHERE status = 'FTBFS' AND date(build_date)<='$DATE';")
	UGLDAY=$(sqlite3 -init ${INIT} ${PACKAGES_DB} "SELECT count(status) from source_packages WHERE status = 'FTBFS' AND date(build_date)='$DATE';")
	REST=$(sqlite3 -init ${INIT} ${PACKAGES_DB} "SELECT count(status) from source_packages WHERE (status != 'FTBFS' AND status != 'FTBFS' AND status != 'unreproducible' AND status != 'reproducible') AND date(build_date)<='$DATE';")
	RESDAY=$(sqlite3 -init ${INIT} ${PACKAGES_DB} "SELECT count(status) from source_packages WHERE (status != 'FTBFS' AND status != 'FTBFS' AND status != 'unreproducible' AND status != 'reproducible') AND date(build_date)='$DATE';")
	OLDESTG=$(sqlite3 -init ${INIT} ${PACKAGES_DB} "SELECT build_date FROM source_packages WHERE status = 'reproducible' AND NOT date(build_date)>='$DATE' ORDER BY build_date LIMIT 1;")
	OLDESTB=$(sqlite3 -init ${INIT} ${PACKAGES_DB} "SELECT build_date FROM source_packages WHERE status = 'unreproducible' AND NOT date(build_date)>='$DATE' ORDER BY build_date LIMIT 1;")
	OLDESTU=$(sqlite3 -init ${INIT} ${PACKAGES_DB} "SELECT build_date FROM source_packages WHERE status = 'FTBFS' AND NOT date(build_date)>='$DATE' ORDER BY build_date LIMIT 1;")
	DIFFG=$(sqlite3 -init ${INIT} ${PACKAGES_DB} "SELECT julianday('$DATE') - julianday('$OLDESTG');")
	if [ -z $DIFFG ] ; then DIFFG=0 ; fi
	DIFFB=$(sqlite3 -init ${INIT} ${PACKAGES_DB} "SELECT julianday('$DATE') - julianday('$OLDESTB');")
	if [ -z $DIFFB ] ; then DIFFB=0 ; fi
	DIFFU=$(sqlite3 -init ${INIT} ${PACKAGES_DB} "SELECT julianday('$DATE') - julianday('$OLDESTU');")
	if [ -z $DIFFU ] ; then DIFFU=0 ; fi
	let "TOTAL=GOOD+BAD+UGLY+REST"
	let "UNTESTED=ALL-TOTAL"
	sqlite3 -init ${INIT} ${PACKAGES_DB} "INSERT INTO ${TABLE[0]} VALUES (\"$DATE\", \"$SUITE\", $UNTESTED, $GOOD, $BAD, $UGLY, $REST)" 
	sqlite3 -init ${INIT} ${PACKAGES_DB} "INSERT INTO ${TABLE[1]} VALUES (\"$DATE\", \"$SUITE\", $GOOAY, $BAAY, $UGLDAY, $RESDAY)"
	sqlite3 -init ${INIT} ${PACKAGES_DB} "INSERT INTO ${TABLE[2]} VALUES (\"$DATE\", \"$SUITE\", \"$DIFFG\", \"$DIFFB\", \"$DIFFU\")"
	# FIXME: we don't do 2 / stats_builds_age.png yet :/ (and do 3 later)
	for i in 0 1 4 5 6 ; do
		# force regeneration of the image
		touch -d "$DATE 00:00" ${TABLE[$i]}.png
	done
	# gather notes stats
	# FIXME: hard-coding another job path is meh
	NOTES=$(grep -c -v "^ " /var/lib/jenkins/jobs/reproducible_html_notes/workspace/packages.yml)
	sqlite3 -init ${INIT} ${PACKAGES_DB} "INSERT INTO ${TABLE[4]} VALUES (\"$DATE\", \"$NOTES\")"
	ISSUES=$(grep -c -v "^ " /var/lib/jenkins/jobs/reproducible_html_notes/workspace/issues.yml)
	sqlite3 -init ${INIT} ${PACKAGES_DB} "INSERT INTO ${TABLE[5]} VALUES (\"$DATE\", \"$ISSUES\")"
fi

# FIXME: work in progress: meta package state graphs
META_PKG="required"
RESULT=$(sqlite3 -init ${INIT} ${PACKAGES_DB} "SELECT datum,meta_pkg,suite from ${TABLE[6]} WHERE datum = \"$DATE\" AND suite = \"$SUITE\" AND meta_pkg = \"$META_PKG\"")
if [ -z $RESULT ] ; then
	META_TOTAL=0
	META_REQUIRED="acl attr base-files base-passwd bash coreutils dash debconf debianutils diffutils dpkg e2fsprogs eglibc findutils gcc-4.7 grep gzip hostname liblocale-gettext-perl libselinux libsepol libtext-charwidth-perl libtext-iconv-perl libtext-wrapi18n-perl lsb mawk ncurses pam perl sed sensible-utils shadow sysvinit tar tzdata util-linux xz-utils zlib"
	META_WHERE=""
	for i in $META_REQUIRED ; do
		if [ -z "$META_WHERE" ] ; then
			META_WHERE="name in ('$i'"
		else
			META_WHERE="$META_WHERE, '$i'"
		fi
	done
	META_WHERE="$META_WHERE)"
	META_GOOD=$(sqlite3 -init ${INIT} ${PACKAGES_DB} "SELECT count(status) from source_packages WHERE status = 'reproducible' AND date(build_date)<='$DATE' AND $META_WHERE;")
	META_BAD=$(sqlite3 -init ${INIT} ${PACKAGES_DB} "SELECT count(status) from source_packages WHERE status = 'unreproducible' AND date(build_date)<='$DATE' AND $META_WHERE;")
	META_UGLY=$(sqlite3 -init ${INIT} ${PACKAGES_DB} "SELECT count(status) from source_packages WHERE status = 'FTBFS' AND date(build_date)<='$DATE' AND $META_WHERE;")
	META_REST=$(sqlite3 -init ${INIT} ${PACKAGES_DB} "SELECT count(status) from source_packages WHERE (status != 'FTBFS' AND status != 'FTBFS' AND status != 'unreproducible' AND status != 'reproducible') AND date(build_date)<='$DATE' AND $META_WHERE;")
	let "META_UNTESTED=META_TOTAL-META_GOOD-META_BAD-META_UGLY-META-REST"
	sqlite3 -init ${INIT} ${PACKAGES_DB} "INSERT INTO ${TABLE[6]} VALUES (\"$DATE\", \"$SUITE\", \"$META_PKG\", $META_UNTESTED, $META_GOOD, $META_BAD, $META_UGLY, $META_REST)" 
fi

# query bts
USERTAGS="toolchain infrastructure timestamps fileordering buildpath username hostname uname randomness"
RESULT=$(sqlite3 -init ${INIT} ${PACKAGES_DB} "SELECT * from ${TABLE[3]} WHERE datum = \"$DATE\"")
if [ -z $RESULT ] ; then
	declare -a DONE
	declare -a OPEN
	SQL="INSERT INTO ${TABLE[3]} VALUES (\"$DATE\" "
	for TAG in $USERTAGS ; do
		OPEN[$TAG]=$(bts select usertag:$TAG users:reproducible-builds@lists.alioth.debian.org status:open status:forwarded 2>/dev/null|wc -l)
		DONE[$TAG]=$(bts select usertag:$TAG users:reproducible-builds@lists.alioth.debian.org status:done archive:both 2>/dev/null|wc -l)
		# test if both values are integers
		if ! ( [[ ${DONE[$TAG]} =~ ^-?[0-9]+$ ]] && [[ ${OPEN[$TAG]} =~ ^-?[0-9]+$ ]] ) ; then
			echo "Non-integers value detected, exiting."
			echo "Usertag: $TAG"
			echo "Open: ${OPEN[$TAG]}"
			echo "Done: ${DONE[$TAG]}"
			exit 1
		fi
		SQL="$SQL, ${OPEN[$TAG]}, ${DONE[$TAG]}"
	done
	SQL="$SQL)"
	echo $SQL
	sqlite3 -init ${INIT} ${PACKAGES_DB} "$SQL"
	# force regeneration of the image
	touch -d "$DATE 00:00" ${TABLE[3]}.png
fi

# used for redo_png (but only needed to define once)
FIELDS[0]="datum, reproducible, unreproducible, FTBFS, other, untested"
FIELDS[1]="datum, reproducible, unreproducible, FTBFS, other"
FIELDS[2]="datum, oldest_reproducible, oldest_unreproducible, oldest_FTBFS"
FIELDS[3]="datum "
for TAG in $USERTAGS ; do
	FIELDS[3]="${FIELDS[3]}, open_$TAG, done_$TAG"
done
FIELDS[4]="datum, packages_with_notes"
FIELDS[5]="datum, known_issues"
FIELDS[6]="datum, reproducible, unreproducible, FTBFS, other, untested"
COLOR[0]=5
COLOR[1]=4
COLOR[2]=3
COLOR[3]=18
COLOR[4]=1
COLOR[5]=1
COLOR[6]=5
MAINLABEL[0]="Package reproducibility status"
MAINLABEL[1]="Amount of packages build each day"
MAINLABEL[2]="Age in days of oldest kind of logfile"
MAINLABEL[3]="Bugs with usertags for user reproducible-builds@lists.alioth.debian.org"
MAINLABEL[4]="Packages which have notes"
MAINLABEL[5]="Identified issues"
MAINLABEL[6]="Package reproducibility status for $META_PKG packages"
YLABEL[0]="Amount (total)"
YLABEL[1]="Amount (per day)"
YLABEL[2]="Age in days"
YLABEL[3]="Amount of bugs"
YLABEL[4]="Amount of packages"
YLABEL[5]="Amount of issues"
YLABEL[6]="Amount ($META_PKG packages)"

redo_png() {
	echo "${FIELDS[$i]}" > ${TABLE[$i]}.csv
	# TABLE[3+4+5] don't have a suite column...
	# 6 is special anyway
	if [ $i -eq 6 ] ; then
		WHERE_EXTRA="WHERE suite = '$SUITE' and meta_pkg = '$META_PKG'"
	elif [ $i -ne 3 ] && [ $i -ne 4 ] && [ $i -ne 5 ] ; then
		WHERE_EXTRA="WHERE suite = '$SUITE'"
	else
		WHERE_EXTRA=""
	fi
	sqlite3 -init ${INIT} -csv ${PACKAGES_DB} "SELECT ${FIELDS[$i]} from ${TABLE[$i]} ${WHERE_EXTRA} ORDER BY datum" >> ${TABLE[$i]}.csv
	/srv/jenkins/bin/make_graph.py ${TABLE[$i]}.csv ${TABLE[$i]}.png ${COLOR[$i]} "${MAINLABEL[$i]}" "${YLABEL[$i]}"
	rm ${TABLE[$i]}.csv
	mv ${TABLE[$i]}.png /var/lib/jenkins/userContent/
}

write_usertag_table() {
	RESULT=$(sqlite3 -init ${INIT} ${PACKAGES_DB} "SELECT * from ${TABLE[3]} WHERE datum = \"$DATE\"")
	if [ -z "$RESULTS" ] ; then
		COUNT=0
		for FIELD in $(echo ${FIELDS[3]} | tr -d ,) ; do
			let "COUNT+=1"
			VALUE=$(echo $RESULT | cut -d "|" -f$COUNT)
			if [ $COUNT -eq 1 ] ; then
				write_page "<table class=\"body\"><tr><th colspan=\"3\">Bugs with usertags for reproducible-builds@lists.alioth.debian.org on $VALUE</th></tr>"
			elif [ $((COUNT%2)) -eq 0 ] ; then
				write_page "<tr><td><a href=\"https://bugs.debian.org/cgi-bin/pkgreport.cgi?tag=${FIELD:5};users=reproducible-builds@lists.alioth.debian.org&archive=both\">${FIELD:5}</a></td><td>Open: $VALUE</td>"
			else
				write_page "<td>Done: $VALUE</td></tr>"
			fi
		done
		write_page "</table>"
	fi
}

VIEW=stats
PAGE=index_${VIEW}.html
echo "$(date) - starting to write $PAGE page."
write_page_header $VIEW "Overview of ${SPOKENTARGET[$VIEW]}"
write_page "<p>"
set_icon reproducible
write_icon
write_page "$COUNT_GOOD packages ($PERCENT_GOOD%) successfully built reproducibly."
set_icon unreproducible with
write_icon
set_icon unreproducible
write_icon
write_page "$COUNT_BAD packages ($PERCENT_BAD%) failed to built reproducibly."
set_icon FTBFS
write_icon
write_page "$COUNT_UGLY packages ($PERCENT_UGLY%) failed to build from source.</p>"
write_page "<p>"
if [ $COUNT_SOURCELESS -gt 0 ] ; then
	write_page "For "
	set_icon 404
	write_icon
	write_page "$COUNT_SOURCELESS ($PERCENT_SOURCELESS%) packages sources could not be downloaded,"
fi
set_icon not_for_us
write_icon
write_page "$COUNT_NOTFORUS ($PERCENT_NOTFORUS%) packages which are neither Architecture: 'any', 'all', 'amd64', 'linux-any', 'linux-amd64' nor 'any-amd64' will not be build here"
write_page "and those "
set_icon blacklisted
write_icon
write_page "$COUNT_BLACKLISTED blacklisted packages neither.</p>"
write_page "<p>"
# FIXME: we don't do 2 / stats_builds_age.png yet :/ (also see above)
for i in 0 3 4 5 6 1 ; do
	if [ "$i" = "3" ] ; then
		write_usertag_table
	fi
	write_page " <a href=\"/userContent/${TABLE[$i]}.png\"><img src=\"/userContent/${TABLE[$i]}.png\" class=\"graph\" alt=\"${MAINLABEL[$i]}\"></a>"
	# redo pngs once a day
	if [ ! -f /var/lib/jenkins/userContent/${TABLE[$i]}.png ] || [ -z $(find /var/lib/jenkins/userContent -maxdepth 1 -mtime +0 -name ${TABLE[$i]}.png) ] ; then
		redo_png
	fi
done
write_page "</p>"
write_page_footer
publish_page

