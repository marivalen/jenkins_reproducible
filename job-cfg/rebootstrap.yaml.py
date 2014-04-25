#!/usr/bin/python

architectures = """
   arm arm64 armel armhf
   i386
   hppa
   mips mipsel
   powerpc powerpcspe ppc64 ppc64el
   s390 s390x
   x32
   """.split()

mono_architectures = """
    alpha
    ia64
    m68k
    or1k
    """.split()

architectures += mono_architectures

gcc_versions = """4.8 4.9""".split()

print("""
- defaults:
    name: rebootstrap
    project-type: freestyle
    properties:
      - sidebar:
          url: https://jenkins.debian.net/userContent/about.html
          text: About jenkins.debian.net
          icon: /userContent/images/debian-swirl-24x24.png
      - sidebar:
          url: https://jenkins.debian.net/view/rebootstrap/
          text: All rebootstrap jobs
          icon: /userContent/images/debian-jenkins-24x24.png
      - sidebar:
          url: http://www.profitbricks.com
          text: Sponsored by Profitbricks
          icon: /userContent/images/profitbricks-24x24.png
      - priority:
          job-prio: '150'
      - throttle:
          max-total: 2
          max-per-node: 2
          enabled: True
          option: category
          categories:
            - rebootstrap
    description: '{my_description}{do_not_edit}'
    logrotate:
      daysToKeep: 365
      numToKeep: 365
      artifactDaysToKeep: -1
      artifactNumToKeep: -1
    scm:
      - git:
          url: 'git://anonscm.debian.org/users/helmutg/rebootstrap.git'
          branches:
            - '{my_branchname}'
    builders:
      - shell: '/srv/jenkins/bin/chroot-run.sh sid ./bootstrap.sh HOST_ARCH={my_arch} {my_params}'
    publishers:
      - email:
          recipients: 'jenkins+debian-bootstrap helmutg@debian.org holger@layer-acht.org'
      - logparser:
          parse-rules: '/srv/jenkins/logparse/rebootstrap.rules'
          unstable-on-warning: 'false'
          fail-on-error: 'false'
    triggers:
      - pollscm: '*/6 * * * *'
""")

for arch in architectures:
    for gccver in gcc_versions:
        for nobiarch in ["", "_nobiarch"]:
            print("""
- job-template:
    defaults: rebootstrap
    name: '{name}_%(arch)s_gcc%(gccshortver)s%(nobiarch)s'""" %
    dict(arch=arch, gccshortver=gccver.replace(".", ""), nobiarch=nobiarch))

print("""
- project:
    name: rebootstrap
    do_not_edit: '<br><br>Job configuration source is <a href="http://anonscm.debian.org/gitweb/?p=qa/jenkins.debian.net.git;a=blob;f=job-cfg/rebootstrap.yaml.py">rebootstrap.yaml.py</a>.'
    jobs:""")
for arch in architectures:
    for gccver in gcc_versions:
        for nobiarch in (False,) if arch in mono_architectures else (False, True):
            print(
"""        - '{name}_%(suffix)s':
            my_arch: '%(arch)s'
            my_params: 'GCC_VER=%(gccver)s ENABLE_MULTILIB=%(multilib_value)s'
            my_description: 'Verify bootstrappability of Debian using gcc-%(gccver)s%(nobiarch_comment)s for %(arch)s'
            my_branchname: 'jenkins_%(suffix)s'""" %
                dict(arch=arch,
                     suffix=arch + "_gcc" + gccver.replace(".", "") + ("_nobiarch" if nobiarch else ""),
                     gccver=gccver,
                     multilib_value="no" if nobiarch else "yes",
                     nobiarch_comment=" without multilib" if nobiarch else ""))