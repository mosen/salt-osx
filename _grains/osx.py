# -*- coding: utf-8 -*-
'''
    OSX/Darwin Specific Grains.

    Grains that relate to the operating system/platform
'''
import salt.utils
import salt.modules.cmdmod
import logging

log = logging.getLogger(__name__)

__virtualname__ = 'mac'

def __virtual__():
    if salt.utils.is_darwin():
        return __virtualname__
    else:
        return False

# Chicken and egg problem, SaltStack style
# __salt__ is already populated with grains by this stage.
cmdmod = {
    'cmd.run': salt.modules.cmdmod._run_quiet,
    # 'cmd.retcode': salt.modules.cmdmod._retcode_quiet,
    'cmd.run_all': salt.modules.cmdmod._run_all_quiet
}

def filevault_enabled():
    """Find out whether FileVault is enabled, via fdesetup.

    :return: True or False
    :rtype: bool
    """
    fv_status = cmdmod['cmd.run']('fdesetup status')
    grains = {}

    if fv_status == 'FileVault is On.':
        grains['filevault_enabled'] = True
    else:
        grains['filevault_enabled'] = False

    return grains


def java_vendor():
    """Get the current Java vendor for the JRE.

    :return: 'Oracle' or 'Apple'
    :rtype: string
    """
    bundle_id = cmdmod['cmd.run']('/usr/bin/defaults read "/Library/Internet Plug-Ins/JavaAppletPlugin.plugin/Contents/Info" CFBundleIdentifier 2>/dev/null')

    if bundle_id == "com.oracle.java.JavaAppletPlugin":
        return 'Oracle'
    elif bundle_id == "com.apple.java.JavaAppletPlugin":
        return 'Apple'


def java_version():
    """Get the current Java version for the JRE.

    :return: The current Java version
    :rtype: string
    """
    bundle_version = cmdmod['cmd.run']('/usr/bin/defaults read "/Library/Internet Plug-Ins/JavaAppletPlugin.plugin/Contents/Info" CFBundleVersion 2>/dev/null')

    return bundle_version


