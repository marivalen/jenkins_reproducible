#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright © 2015 Mattia Rizzolo <mattia@mapreri.org>
# Based on reproducible_html_packages.sh © 2014 Holger Levsen <holger@layer-acht.org>
# Licensed under GPL-2
#
# Depends: python3
#
# Build rb-pkg pages (the pages that describe the package status)

from reproducible_common import *

html_package_page = Template((tab*2).join(("""
<table class="head">
    <tr>
        <td>
            <span style="font-size:1.2em;">$package</span> $version
$status
            <span style="font-size:0.9em;">$build_time:</span>
$links
            <a href="https://tracker.debian.org/$package" target="main">PTS</a>
            <a href="https://bugs.debian.org/src:$package" target="main">BTS</a>
            <a href="https://sources.debian.net/src/$package/" target="main">sources</a>
            <a href="https://sources.debian.net/src/$package/$version/debian/" target="main">debian</a>/<!--
            -->{<a href="https://sources.debian.net/src/$package/$version/debian/changelog" target="main">changelog</a>,<!--
            --><a href="https://sources.debian.net/src/$package/$version/debian/rules" target="main">rules</a>}
        </td>
        <td>
${suites_links}
        </td>
        <td style="text-align:right; font-size:0.9em;">
            <a href="%s" target="_parent">
                reproducible builds
            </a>
        </td>
    </tr>
</table>
<iframe id="main" name="main" src="${default_view}">
    <p>
        Your browser does not support iframes.
        Use a different one or follow the links above.
    </p>
</iframe>""" % REPRODUCIBLE_URL ).splitlines(True)))


def sizeof_fmt(num):
    for unit in ['B','KB','MB','GB']:
        if abs(num) < 1024.0:
            if unit == 'GB':
                log.error('The size of this file is bigger than 1 GB!')
                log.error('Please check')
            return str(int(round(float("%3f" % num), 0))) + "%s" % (unit)
        num /= 1024.0
    return str(int(round(float("%f" % num), 0))) + "%s" % ('Yi')

def check_package_status(package, suite, nocheck=False):
    """
    This returns a tuple containing status, version and build_date of the last
    version of the package built by jenkins CI
    """
    try:
        query = ('SELECT r.status, r.version, r.build_date ' +
                 'FROM results AS r JOIN sources AS s ON r.package_id=s.id ' +
                 'WHERE s.name="{pkg}" ' +
                 'AND s.suite="{suite}"').format(pkg=package, suite=suite)
        result = query_db(query)[0]
    except IndexError:
        query = 'SELECT version FROM sources WHERE name="{pkg}" AND suite="{suite}"'
        query = query.format(pkg=package, suite=suite)
        try:
            result = query_db(query)[0][0]
            if result:
                result = ('untested', str(result), False)
        except IndexError:
            if nocheck:
                return False
            print_critical_message('This query produces no results: ' + query +
                    '\nThis means there is no available package with the name '
                    + package + '.')
            raise
    status = str(result[0])
    version = str(result[1])
    if result[2]:
        build_date = 'at ' + str(result[2]) + ' UTC'
    else:
        build_date = '<span style="color:red;font-weight:bold;">UNTESTED</span>'
    return (status, version, build_date)


def gen_status_link_icon(status, icon, suite, arch):
    html = ''
    if status != 'untested':
        html += tab*6 + '<a href="/{suite}/{arch}/index_{status}.html"' + \
                ' target="_parent" title="{status}">\n'
    html += tab*9 + '<img src="/static/{icon}" alt="{status}" />\n'
    if status != 'untested':
        html += tab*8 + '</a>\n'
    return html.format(status=status, icon=icon, suite=suite, arch=arch)


def gen_extra_links(package, version, suite, arch):
    eversion = strip_epoch(version)
    notes = NOTES_PATH + '/' + package + '_note.html'
    rbuild = RBUILD_PATH + '/' + suite + '/' + arch + '/' + package + '_' + \
             eversion + '.rbuild.log'
    buildinfo = BUILDINFO_PATH + '/' + suite + '/' + arch + '/' + package + \
                '_' + eversion + '_amd64.buildinfo'
    dbd = DBD_PATH + '/' + suite + '/' + arch + '/' + package + '_' + \
          eversion + '.debbindiff.html'

    links = ''
    default_view = ''
    # check whether there are notes available for this package
    if os.access(notes, os.R_OK):
        url = NOTES_URI + '/' + package + '_note.html'
        links += '<a href="' + url + '" target="main">notes</a>\n'
        default_view = url
    else:
        log.debug('notes not detected at ' + notes)
    if os.access(dbd, os.R_OK):
        url = DBD_URI + '/' + suite + '/' + arch + '/' +  package + '_' + \
              eversion + '.debbindiff.html'
        links += '<a href="' + url + '" target="main">debbindiff</a>\n'
        if not default_view:
            default_view = url
    else:
        log.debug('debbindiff not detetected at ' + dbd)
    if pkg_has_buildinfo(package, version, suite):
        url = BUILDINFO_URI + '/' + suite + '/' + arch + '/' + package + \
              '_' + eversion + '_amd64.buildinfo'
        links += '<a href="' + url + '" target="main">buildinfo</a>\n'
        if not default_view:
            default_view = url
    else:
        log.debug('buildinfo not detected at ' + buildinfo)
    if os.access(rbuild, os.R_OK):
        url = RBUILD_URI + '/' + suite + '/' + arch + '/' + package + '_' + \
              eversion + '.rbuild.log'
        log_size = os.stat(rbuild).st_size
        links +='<a href="' + url + '" target="main">rbuild (' + \
                sizeof_fmt(log_size) + ')</a>\n'
        if not default_view:
            default_view = url
    else:
        log.warning('The package ' + package +
                    ' did not produce any buildlog! Check ' + rbuild)
    default_view = '/untested.html' if not default_view else default_view
    return (links, default_view)


def gen_suites_links(package, suite):
    html = ''
    query = 'SELECT s.suite, s.architecture, r.status ' + \
            'FROM sources AS s LEFT JOIN results AS r ON r.package_id=s.id ' + \
            'WHERE s.name="{pkg}"'.format(pkg=package)
    results = query_db(query)
    if len(results) < 1:
        print_critical_message('This query produces 0 results:\n' + query)
        raise ValueError
    if len(results) == 1:
        return html
    for i in results:
        # i[0]: suite, i[1]: arch, i[2]: status (NULL if untested)
        if i[0] == suite:
            continue
        status = 'untested' if not i[2] else i[2]
        icon = '<img src="/static/{icon}" alt="{status}" title="{status}"/>\n'
        html += icon.format(icon=join_status_icon(status)[1], status=status)
        html += '<a href="' + RB_PKG_URI + '/' + i[0] + '/' + i[1] + '/' + \
                str(package) + '.html" target="_parent">' + i[0] + '</a> '
    return tab*5 + (tab*7).join(html.splitlines(True))


def gen_packages_html(packages, suite=None, arch=None, no_clean=False, nocheck=False):
    """
    generate the /rb-pkg/package.html page
    packages should be a list
    If suite and/or arch is not passed, then build that packages for all suites
    nocheck is for internal use
    """
    total = len(packages)
    log.info('Generating the pages of ' + str(total) + ' package(s)')
    if not nocheck and (not suite or not arch):
        nocheck = True
    if nocheck and (not suite or not arch):
        for lsuite in SUITES:
            for larch in ARCHES:
                gen_packages_html(packages, lsuite, larch, no_clean, True)
        return
    for pkg in sorted(packages):
        pkg = str(pkg)
        try:
            status, version, build_date = check_package_status(pkg, suite, nocheck)
        except TypeError:  # the package is not in the checked suite
            continue
        log.info('Generating the page of ' + pkg + '/' + suite + '@' + version +
                 ' built at ' + build_date)

        links, default_view = gen_extra_links(pkg, version, suite, arch)
        suites_links = gen_suites_links(pkg, suite)
        status, icon = join_status_icon(status, pkg, version)
        status = gen_status_link_icon(status, icon, suite, arch)

        html = html_package_page.substitute(package=pkg,
                                            status=status,
                                            version=version,
                                            build_time=build_date,
                                            links=links,
                                            suites_links=suites_links,
                                            default_view=default_view)
        destfile = RB_PKG_PATH + '/' + suite + '/' + arch + '/' + pkg + '.html'
        desturl = REPRODUCIBLE_URL + RB_PKG_URI + '/' + suite + '/' + \
                  arch + '/' + pkg + '.html'
        title = pkg + ' - reproducible build results'
        write_html_page(title=title, body=html, destfile=destfile, suite=suite,
                        noheader=True, noendpage=True)
        log.info("Package page generated at " + desturl)
    if not no_clean:
        purge_old_pages() # housekeep is always good

def gen_all_rb_pkg_pages(suite='sid', arch='amd64', no_clean=False):
    query = 'SELECT name FROM sources WHERE suite="%s" AND architecture="%s"' % (suite, arch)
    rows = query_db(query)
    pkgs = [str(i[0]) for i in rows]
    log.info('Processing all the package pages, ' + str(len(pkgs)))
    gen_packages_html(pkgs, suite=suite, arch=arch, no_clean=no_clean)

def purge_old_pages():
    for suite in SUITES:
        for arch in ARCHES:
            log.info('Removing old pages from ' + suite + '/' + arch + '...')
            try:
                presents = sorted(os.listdir(RB_PKG_PATH + '/' + suite + '/' +
                                  arch))
            except OSError as e:
                if e.errno != errno.ENOENT:  # that's 'No such file or
                    raise                    # directory' error (errno 17)
                presents = []
            log.debug('page presents: ' + str(presents))
            for page in presents:
                pkg = page.rsplit('.', 1)[0]
                query = 'SELECT s.name ' + \
                    'FROM sources AS s ' + \
                    'WHERE s.name="{name}" ' + \
                    'AND s.suite="{suite}" AND s.architecture="{arch}"'
                query = query.format(name=pkg, suite=suite, arch=arch)
                result = query_db(query)
                if not result: # actually, the query produces no results
                    log.info('There is no package named ' + pkg + ' from ' +
                             suite + '/' + arch + ' in the database. ' +
                             'Removing old page.')
                    os.remove(RB_PKG_PATH + '/' + suite + '/' + arch + '/' +
                              page)

