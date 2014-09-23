#!/bin/bash

# Copyright 2014 Holger Levsen <holger@layer-acht.org>
# released under the GPLv=2

. /srv/jenkins/bin/common-functions.sh
common_init "$@"

TMPFILE=$(mktemp=)
cat > $TMPFILE <<- EOF
echo 'deb http://reproducible.alioth.debian.org/debian/ ./' > /etc/apt/sources.list.d/reproducible.list
apt-get update
apt-get install -y dpkg dpkg-dev debhelper dh-python proot
EOF

sudo cp /var/cache/pbuilder/base.tgz /var/cache/pbuilder/base-reproducible.tgz
sudo pbuilder --execute $TMPFILE --save-after-exec --basetgz /var/cache/pbuilder/base-reproducible.tgz
rm $TMPFILE
