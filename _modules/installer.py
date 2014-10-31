# -*- coding: utf-8 -*-
"""
Install packages using the osx 'installer' tool.

:maintainer:    Mosen <mosen@github.com>
:maturity:      new
:depends:       cmdmod
:platform:      darwin

Large amounts of this module are lifted from gneagle's excellent munki tools project. Without which the mac admin
community may not exist in its current form.

This is not munki, but it should be enough to bootstrap a mac client at least, to the point where munki can take over.

Support for pkg.installed:
- name: not used to identify the package because using the pkgid would not always give us the correct result.
- fromrepo: won't be supported
- skip_verify: might be able to check against SHA256 hashes in yaml
- skip_suggestions: n/a
- version: n/a
- allow_updates: we could respect this
- pkg_verify: v2
- pkgs: not supported
- names: not supported
- sources: yes

Support for pkg.verify?
Support for pkg.list_pkgs
Support pkg.purge/remove?
"""

import os
import pwd
import subprocess
import time
import stat
import re

import logging

import salt.utils

log = logging.getLogger(__name__)

__virtualname__ = 'installer'

def __virtual__():
    return __virtualname__ if salt.utils.is_darwin() else False


def _install_pkg(pkgpath, choicesXMLpath=None, suppressBundleRelocation=False,
             environment=None):
    '''
    Install a single package using the apple installer tool.

    Notable omissions from munkilib:
    - pkginfo
    - package relocation
    '''
    restartneeded = False
    environment = None

    if os.path.islink(pkgpath):
        # resolve links before passing them to /usr/bin/installer - munki
        pkgpath = os.path.realpath(pkgpath)

    restartaction = 'None'
    packagename = os.path.basename(pkgpath)
    log.debug("Installing %s from %s" % (packagename, os.path.basename(pkgpath)))

    cmd = ['/usr/sbin/installer', '-query', 'RestartAction', '-pkg', pkgpath]
    if choicesXMLpath:
        cmd.extend(['-applyChoiceChangesXML', choicesXMLpath])
    proc = subprocess.Popen(cmd, shell=False, bufsize=1,
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (output, unused_err) = proc.communicate()
    restartaction = str(output).decode('UTF-8').rstrip("\n")
    if restartaction == "RequireRestart" or \
        restartaction == "RecommendRestart":
        log.debug('%s requires a restart after installation.' % packagename)
        restartneeded = True

    os_version = __grains__['osrelease']

    cmd = ['/usr/sbin/installer', '-verboseR', '-pkg', pkgpath,
           '-target', '/']
    if choicesXMLpath:
        cmd.extend(['-applyChoiceChangesXML', choicesXMLpath])

    # set up environment for installer
    env_vars = os.environ.copy()
    # get info for root
    userinfo = pwd.getpwuid(0)
    env_vars['USER'] = userinfo.pw_name
    env_vars['HOME'] = userinfo.pw_dir
    if environment:
        # Munki admin has specified custom installer environment
        for key in environment.keys():
            if key == 'USER' and environment[key] == 'CURRENT_CONSOLE_USER':
                # current console user (if there is one) 'owns' /dev/console
                userinfo = pwd.getpwuid(os.stat('/dev/console').st_uid)
                env_vars['USER'] = userinfo.pw_name
                env_vars['HOME'] = userinfo.pw_dir
            else:
                env_vars[key] = environment[key]
                log.debug(
                    'Using custom installer environment variables: %s', env_vars)

    # instead of creating a launchd dictionary and submitting the job to run, we use subprocess.
    # this has the negative side effect of breaking office update packages. (waits at finishing stage).
    # See 2012 discussion RE office update: https://groups.google.com/forum/#!topic/munki-dev/MbNCxvf-NfQ/discussion
    proc = subprocess.Popen(cmd, shell=False, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (output, err) = proc.communicate()
    log.error(err)
    log.debug(output)

    if proc.returncode != 0:
        log.error('Install of %s failed with return code %s' % (packagename, proc.returncode))
        restartneeded = False

    return (proc.returncode, restartneeded)


def install(name=None,
            sources=None,
            **kwargs):
    '''
    Install the package using the OSX ``installer`` tool.

    name
        This argument is mostly ignored on OSX, since there is no key identifier for a package.
        Typically you could use the bundle id, but this is not always reliable.

        CLI Example:

        .. code-block:: bash

            salt '*' pkg.install <package name>


    Multiple Package Installation Options:

    sources
        A list of pkg or mpkg packages to install. Must be passed as a list of dicts,
        with the keys being package names, and the values being the source URI
        or local path to the package.

        CLI Example:

        .. code-block:: bash

            salt '*' pkg.install sources='[{"foo": "salt://foo.pkg"},{"bar": "salt://bar.mpkg"}]'

    Returns a dict containing the new package names and versions::

        {'<package>': {'old': '<old-version>',
                       'new': '<new-version>'}}
    '''
    # loop through sources, run _install


def list_pkgs(versions_as_list=False,
              **kwargs):
    '''
    List the packages currently installed in a dict::

        {'<package_name>': '<version>'}

    .. note:: Supported parameters

        This module does not support querying for removed or packages to be purged.

    CLI Example:

    .. code-block:: bash

        salt '*' pkg.list_pkgs
        salt '*' pkg.list_pkgs versions_as_list=True
    '''
    versions_as_list = salt.utils.is_true(versions_as_list)

    ret = {'installed': {}}
    result = __salt__['cmd.run']('/usr/sbin/pkgutil --regexp --pkg-info-plist ".*"')
    plist_strings = re.split(r'\n\n', result)
    log.debug("%d strings" % len(plist_strings))
    plists = [__salt__['plist.parse_string'](plist_string) for plist_string in plist_strings]
    log.debug("%d plists" % len(plists))

    packages = {plist.objectForKey_('pkgid'): plist.objectForKey_('pkg-version') for plist in plists}

    # Now check /Library/Receipts for older packages?
    receiptsdir = '/Library/Receipts'
    if os.path.exists(receiptsdir):
        pass

    return packages
