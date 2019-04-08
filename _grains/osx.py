# -*- coding: utf-8 -*-
'''
    OSX/Darwin Specific Grains.

    Grains that relate to the operating system/platform
'''
import salt.utils
import salt.modules.cmdmod
import logging
import re


log = logging.getLogger(__name__)

__virtualname__ = 'mac'


def __virtual__():
    if salt.utils.platform.is_darwin():
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

def gatekeeper_enabled():
    """Find out whether Gatekeeper is enabled, via spctl."""
    output = cmdmod['cmd.run']('spctl --status')
    if re.search(r"enabled", output):
        return {'gatekeeper_enabled': True}
    else:
        return {'gatekeeper_enabled': False}


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


def sip_enabled():
    '''
    Determine the status of System Integrity Protection.
    '''
    sip_status = cmdmod['cmd.run']('csrutil status')

    if re.match(r'disabled', sip_status) is None:
        return {'sip_enabled': True}
    else:
        return {'sip_enabled': False}


def java_vendor():
    """Get the current Java vendor for the JRE.

    :return: 'Oracle' or 'Apple'
    :rtype: string
    """
    bundle_id = cmdmod['cmd.run'](
        '/usr/bin/defaults read "/Library/Internet Plug-Ins/JavaAppletPlugin.plugin/Contents/Info" CFBundleIdentifier 2>/dev/null')

    if bundle_id == "com.oracle.java.JavaAppletPlugin":
        vendor = 'Oracle'
    elif bundle_id == "com.apple.java.JavaAppletPlugin":
        vendor = 'Apple'

    return {'mac_java_vendor': vendor} if vendor else None


def java_version():
    """Get the current Java version for the JRE.

    :return: The current Java version
    :rtype: string
    """
    bundle_version = cmdmod['cmd.run'](
        '/usr/bin/defaults read "/Library/Internet Plug-Ins/JavaAppletPlugin.plugin/Contents/Info" CFBundleVersion 2>/dev/null')

    return {'mac_java_version': bundle_version} if bundle_version else None


def flash_version():
    """Get the current version of the Flash internet plug-in"""
    output = cmdmod['cmd.run'](
        "/usr/bin/defaults read '/Library/Internet Plug-Ins/Flash Player.plugin/Contents/Info' CFBundleVersion 2>/dev/null")
    return {'mac_flash_version': output} if output else None

def mac_laptop():
    """Determine whether this machine is a laptop or desktop.

    :return: 'mac_laptop' or 'mac_desktop'
    :rtype: string
    """
    model = cmdmod['cmd.run']("sysctl hw.model |awk '{ print $2 }'")
    hardware_type = 'mac_laptop' if re.search('Book', model) else 'mac_desktop'
    return {'mac_laptop': hardware_type}


# def mac_current_user():
#     """Determine currently logged in user.
#
#     :return: short loginname of current user.
#     :rype: string
#     """
#     output = cmdmod['cmd.run']("/bin/ls -l /dev/console | /usr/bin/awk '{ print $3 }'")
#     return {'mac_current_user': output}


def mac_timezone():
    """Determine system timezone"""
    output = cmdmod['cmd.run']("/usr/sbin/systemsetup -gettimezone")
    return {'mac_timezone': output[11:]}
