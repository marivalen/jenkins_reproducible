#!/usr/bin/python

archs = """
    amd64
    arm64
    armel
    armhf
    hurd-i386
    i386
    kfreebsd-amd64
    kfreebsd-i386
    mips
    mipsel
    powerpc
    ppc64el
    s390x
    sparc
   """.split()

print("""
- defaults:
    name: d-i
    project-type: freestyle
    logrotate:
      daysToKeep: 90
      numToKeep: 30
      artifactDaysToKeep: -1
      artifactNumToKeep: -1
    properties:
      - sidebar:
          url: https://jenkins.debian.net/userContent/about.html
          text: About jenkins.debian.net
          icon: /userContent/images/debian-swirl-24x24.png
      - sidebar:
          url: https://jenkins.debian.net/view/d-i_misc/
          text: Misc debian-installer jobs
          icon: /userContent/images/debian-jenkins-24x24.png
      - sidebar:
          url: http://www.profitbricks.com
          text: Sponsored by Profitbricks
          icon: /userContent/images/profitbricks-24x24.png
""")

for arch in sorted(archs):
    print("""- job-template:
    defaults: d-i
    name: '{name}_overview_%(arch)s'
    description: 'Parses d-i build overview for problems on %(arch)s from <code>http://d-i.debian.org/daily-images/daily-build-overview.html</code> daily. {do_not_edit}'
    builders:
      - shell: '/srv/jenkins/bin/d-i_overview.sh %(arch)s'
    triggers:
      - timed: "0 * * * *"
    publishers:
      - logparser:
          parse-rules: '/srv/jenkins/logparse/debian-installer.rules'
          unstable-on-warning: 'true'
          fail-on-error: 'true'
      - email-ext:
          recipients: holger@layer-acht.org
          first-failure: true
          fixed: true
          subject: 'Build results for: $JOB_NAME $BUILD_NUMBER $BUILD_STATUS'
          attach-build-log: true
          body: 'See $BUILD_URL and $BUILD_URL/console and http://d-i.debian.org/daily-images/daily-build-overview.html#%(arch)s'
# FIXME:  recipients: jenkins+debian-boot holger@layer-acht.org
""" % dict(arch=arch))

print("""
- project:
    name: d-i
    do_not_edit: '<br><br>Job configuration source is <a href="http://anonscm.debian.org/cgit/qa/jenkins.debian.net.git/job-cfg/d-i-overview.yaml.py">d-i-overview.yaml.py</a>.'
    jobs:""")
for arch in sorted(archs):
    print("""      - '{name}_overview_%(arch)s'"""
        % dict(arch=arch))




