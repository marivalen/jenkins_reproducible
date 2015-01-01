#!/usr/bin/python

images = """
    wheezy_standard
    wheezy_gnome-desktop
   """.split()

features = """
    apt
   """.split()

files = { 'wheezy_standard': '/var/lib/jenkins/debian-live-7.7.0-amd64-standard.iso',
          'wheezy_gnome-desktop': '/var/lib/jenkins/debian-live-7.7.0-amd64-gnome-desktop.iso'
        }

titles = { 'wheezy_standard': 'Debian Live 7 standard',
           'wheezy_gnome-desktop': 'Debian Live 7 GNOME desktop'
         }

print("""
- defaults:
    name: lvc
    project-type: freestyle
    description: '{my_description}<br><br>Job configuration source is <a href="http://anonscm.debian.org/cgit/qa/jenkins.debian.net.git/tree/job-cfg/lvc.yaml.py">lvc.yaml.py</a>.'
    properties:
      - sidebar:
          url: https://jenkins.debian.net/userContent/about.html
          text: About jenkins.debian.net
          icon: /userContent/images/debian-swirl-24x24.png
      - sidebar:
          url: https://jenkins.debian.net/view/lvc
          text: Jobs for libvirt and cucumber based tests
          icon: /userContent/images/debian-jenkins-24x24.png
      - sidebar:
          url: http://www.profitbricks.com
          text: Sponsored by Profitbricks
          icon: /userContent/images/profitbricks-24x24.png
      - throttle:
          max-total: 1
          max-per-node: 1
          enabled: true
          option: category
          categories:
            - lvc
    logrotate:
      daysToKeep: 90
      numToKeep: 20
      artifactDaysToKeep: -1
      artifactNumToKeep: -1
    publishers:
      - email:
          recipients: 'holger@layer-acht.org'
      - archive:
          artifacts: '*.webm, {my_pngs}'
          latest_only: false
      - imagegallery:
          title: '{my_title}'
          includes: '{my_pngs}'
          image-width: 300
    wrappers:
      - live-screenshot
    builders:
      - shell: '/srv/jenkins/bin/lvc/run_test_suite {my_params}'
    triggers:
      - timed: '{my_time}'
""")

for image in sorted(images):
    for feature in sorted(features):
        print("""- job-template:
    defaults: lvc
    name: '{name}_debian-live_%(image)s_%(feature)s'
""" % dict(image=image,
           feature=feature))

print("""
- project:
    name: lvc
    jobs:""")
for image in sorted(images):
    for feature in sorted(features):
        print("""        - '{name}_debian-live_%(image)s_%(feature)s':
           my_title: '%(title)s'
           my_time: '23 45 31 12 *'
           my_params: '--debug --capture lvc_debian-live_%(image)s_%(feature)s.webm --temp-dir $WORKSPACE --iso %(iso)s DebianLive7/%(feature)s.feature'
           my_pngs: '%(feature)s-*.png'
           my_description: 'Work in progress...'
""" % dict(image=image,
           feature=feature,
           iso=files[image],
           title=titles[image]))
