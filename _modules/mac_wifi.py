# -*- coding: utf-8 -*-
'''
Module for configuring WiFi settings on macOS.

.. note::
        Requires the PyObjC Library that is bundled with the macOS installer
        package as of 2019.2.0.
'''
import salt.utils
import salt.utils.platform
import logging
import sys
import os.path
import collections
from salt.exceptions import CommandExecutionError

log = logging.getLogger(__name__)

try:
    import objc, ctypes.util
    from Foundation import NSOrderedSet
    PYOBJC = True
except ImportError:
    PYOBJC = False

__virtualname__ = 'wifi'


def __virtual__():
    """
    Check if macOS and PyObjC is available
    """
    if not salt.utils.platform.is_darwin():
        return (False, 'module: mac_wifi only available on macOS.')
    if not PYOBJC:
        return (False, 'PyObjC not available.')
    return __virtualname__


def _load_objc_framework(framework_name):
    """
    Utility function that loads a Framework bundle and creates a named tuple
    where the attributes are the loaded classes from the Framework bundle
    """
    log.trace('wifi._load_objc_framework: loading {}.'.format(framework_name))
    loaded_classes = dict()
    framework_bundle = objc.loadBundle(framework_name, bundle_path=os.path.dirname(ctypes.util.find_library(framework_name)), module_globals=loaded_classes)
    loaded_classes = dict([x for x in loaded_classes.items() if not x[0].startswith('_')])
    return collections.namedtuple('AttributedFramework', loaded_classes.keys())(**loaded_classes)

def _get_configuration(CoreWLAN, interface):
    configuration_copy = CoreWLAN.CWMutableConfiguration.alloc().initWithConfiguration_(
        interface.configuration())
    return configuration_copy


def _get_available_wifi_interfaces(CoreWLAN):
    interfaces = dict()
    for name in CoreWLAN.CWInterface.interfaceNames():
        try:
            interfaces[name] = CoreWLAN.CWInterface.interfaceWithName_(name)
        except TypeError:
            # Wifi is either disabled or we're running on a VM with alternate network configs.
            log.trace('module.mac_wifi - Unable to get interface name.')
            continue
    return interfaces


def _get_profiles_and_ssids(configuration):
    # Find all the preferred/remembered network profiles
    try:
        profiles = list(NSOrderedSet.array(configuration.networkProfiles()))
    except TypeError:
        # if we got here we probably don't have any SSIDs in the wifi list
        # we'll return a tuple of empty lists. Theres probably a better way to
        # handle this.
        log.trace('module.mac_wifi - Could not find an SSIDs.')
        return ([], [])
    # Grab all the SSIDs, in order
    SSIDs = [x.ssid() for x in profiles]
    return (profiles, SSIDs)


def _manipulate_wifi(name, func, just_ssids=False, just_profiles=False):
    '''
    The core of this code comes from this gist by Pudquick. Thank you!
    https://gist.github.com/pudquick/fcbdd3924ee230592ab4
    '''
    CoreWLAN = _load_objc_framework('CoreWLAN')
    interfaces = _get_available_wifi_interfaces(CoreWLAN)

    for interface in interfaces.keys():
        # Grab a mutable copy of this interface's configuration
        configuration_copy = CoreWLAN.CWMutableConfiguration.alloc().initWithConfiguration_(
            interfaces[interface].configuration())
        # Find all the preferred/remembered network profiles
        pro_ssid = _get_profiles_and_ssids(configuration_copy)
        profiles = pro_ssid[0]
        SSIDs = pro_ssid[1]

        # return just the profiles.
        if just_profiles:
            return profiles

        # check to see if we want just the list of SSID's
        if just_ssids:
            return SSIDs

        # see if we actually have any SSID's.
        if not SSIDs:
            # we can bounce out since there isn't anything to do with any empty
            # list of SSIDs
            return True

        # takes the function to run here as a parameter, so we can remove, sort,
        # top or bottom.
        profiles = func(name, profiles=profiles)
        # Now we have to update the mutable configuration
        # First convert it back to a NSOrderedSet
        log.trace('wifi._manipulate_wifi: Attempting to set changed WiFi profiles.')
        profile_set = NSOrderedSet.orderedSetWithArray_(profiles)
        # Then set/overwrite the configuration copy's networkProfiles
        configuration_copy.setNetworkProfiles_(profile_set)
        # Then update the network interface configuration
        result = interfaces[interface].commitConfiguration_authorization_error_(configuration_copy, None, None)
    try:
        if result[0] == 1:
            return True
    except Exception as e:
        ret = 'wifi._manipulate_wifi'
        return (False,
                'Caught Exception: {} in parsing return from {}'.format(e, ret))
    return (False, result[1])


def _get_ssids():
    return _manipulate_wifi(None, None, just_ssids=True)


def _get_profiles():
    'returns the Newtork profiles'
    return _manipulate_wifi(None, None, just_profiles=True)


def _top(name, profiles=None):
    '''
    move name to the top of this in reverse order to they appear correctly
    '''

    # sort name to the top.
    log.trace('Attempting to move SSID [{}] to the top.'.format(name))
    profiles.sort(key=lambda x: x.ssid() == name, reverse=True)

    return profiles


def _bottom(name, profiles=None):
    '''
    move name to the bottom of the list in reverse order to they appear correctly
    '''

    log.trace('Attempting to move SSID [{}] to the bottom.'.format(name))
    profiles.sort(key=lambda x: x.ssid() == name, reverse=False)

    return profiles


def _remove(name, profiles=None):
    '''
    remove name from the preferred list.
    '''
    log.trace('called wifi._remove')

    for ssid in profiles:
        if ssid.ssid() == name:
            log.trace('wifi._remove: Removing SSID {} from list.'.format(
                name))
            profiles.remove(ssid)

    return profiles


def _disable_autojoin(name, profiles=None):
    '''
    disables autojoin for the given SSID
    '''
    for ssid in profiles:
        if ssid.ssid() == name:
            log.trace('Disabling AutoJoin for SSID [{}].'.format(name))
            ssid.setDisabled_(True)
            break
    return profiles


def _enable_autojoin(name, profiles=None):
    '''
    disables autojoin for the given SSID
    '''
    for ssid in profiles:
        if ssid.ssid() == name:
            log.trace('Enabling AutoJoin for SSID [{}].'.format(name))
            ssid.setDisabled_(False)
            break
    return profiles


def top(name):
    '''
    Move a SSID to the TOP of the Preffered Networks Order list.

    :param str name: The name of the SSID(s) you would like moved to the top.

    :return: ``True`` if successfully moved to the top, or ``False`` if it
        failed.

    :rtype: bool

    CLI Example:

    .. code-block:: bash

        salt '*' wifi.top PiedPiper
    '''
    return _manipulate_wifi(name, func=_top)


def bottom(name):
    '''
    Move a SSID to the BOTTOM of the Preffered Networks Order list.

    :param str name: The name of the SSID(s) you would like moved to the bottom.

    :return: ``True`` if successfully moved to the bottom, or ``False`` if it
        failed.

    :rtype: bool

    CLI Example:

    .. code-block:: bash

        salt '*' wifi.bottom PiedPiper-Guest
    '''


    log.trace('wifi.bottom called with pramater(s) {}.'.format(name))

    return _manipulate_wifi(name, func=_bottom)


def remove(name):
    '''
    Remove an SSID from the Preferred Networks list.

    :param str name: The name of the SSID you would like moved to the bottom.

    :return: ``True`` if successful, ``False`` on failure.

    :rtype: bool

    CLI Example:

    .. code-block:: bash

        salt '*' wifi.remove Hooli-Guest

    .. note::
        If you would like to add an SSID consider using a macOS profile.
    '''
    # attempt to remove the ssid
    remove_wifi = _manipulate_wifi(name, func=_remove)

    # check to see if it was remove correctly.
    if __salt__['wifi.missing'](name):
        return True
    return False


def exists(name):
    '''
    Check if the provided SSID is in the Preferred Networks list.

    :param str name: The name of the SSID you would like to check exists.

    :return: ``True`` if exists, ``False`` if it doesn't.

    :rtype: bool

    CLI Example:

    .. code-block:: bash

        salt '*' wifi.exists Hooli
    '''

    ssids = _get_ssids()

    if name in ssids:
        return True

    log.trace('SSID "{}" does not exist.'.format(name))
    return False


def missing(name):
    '''
    Check if the provided SSID is not present in the Preferred Networks list.

    :param str name: The name of the SSID you would like to check.

    :return: ``True`` if not available, or ``False`` if it is available.

    :rtype: bool

    CLI Example:

    .. code-block:: bash

        salt '*' wifi.missing Hooli-Guest
    '''
    return not __salt__['wifi.exists'](name)


def ssid_index(name, reverse=False):
    '''
    Get the index number for the provided SSID, for the top of the
    Preferred Networks list.

    :param str name: The name of the SSID.

    :param bool reverse: Set to ``True`` to get the index number
        from the bottom. Defaults to ``False``

    :return: Index number of the SSID from the top or bottom of the
        Preferred Networks list, or ``None`` if not available.

    :rtype: int, None

    CLI Example:

    .. code-block:: bash

        salt '*' wifi.ssid_index Hooli
        salt '*' wifi.ssid_index Hooli reverse=True
    '''

    ssids = _get_ssids()

    if reverse:
        ssids = list(reversed(ssids))

    try:
        return ssids.index(name)
    except ValueError:
        return None


def disable_autojoin(name):
    '''
    Disables the Auto-Join Feature of the provided SSID.

    :param str name: The name of the SSID.

    :return: ``True`` if successful, ``False`` if network doesn't exist or failed.

    :rtype: bool

    CLI Example:

    .. code-block:: bash

        salt '*' wifi.disable_autojoin Hooli
    '''
    if not __salt__['wifi.exists'](name):
        return False
    # disable autojoin
    disable_aj = _manipulate_wifi(name, func=_disable_autojoin)

    log.trace('Checking if SSID [{}] was disabled correctly.'.format(name))
    # check if autojoin was actually disabled properly
    return True if __salt__['wifi.autojoin_disabled'](name) else False


def enable_autojoin(name):
    '''
    Enables the Auto-Join Feature of the provided SSID.

    :param str name: The name of the SSID.

    :return: ``True`` if successful, ``False`` if network doesn't exist or
        failed.

    :rtype: bool

    CLI Example:

    .. code-block:: bash

        salt '*' wifi.enable_autojoin PiedPiper
    '''
    if not __salt__['wifi.exists'](name):
        return False

    enable_aj = _manipulate_wifi(name, func=_enable_autojoin)

    log.trace('Checking if SSID [{}] was enabled correctly.'.format(name))
    # check if autojoin was enabled properly
    return True if __salt__['wifi.autojoin_enabled'](name) else False


def autojoin_disabled(name):
    '''
    Check if the Auto-Join feature is disabled for the given SSID.

    :param str name: The name of the SSID.

    :return: ``True`` if disabled, ``False`` if enabled or not available.

    :rtype: bool

    CLI Example:

    .. code-block:: bash

        salt '*' wifi.disable_autojoin Hooli-Guest
    '''
    profiles = _get_profiles()
    for ssid in profiles:
        if ssid.ssid() == name:
            log.trace('Found network profile for SSID [{}].'.format(name))
            if ssid.disabled():
                return True
            return False

    log.debug('Could not find profile for [{}].'.format(name))
    return False


def autojoin_enabled(name):
    '''
    Check if the Auto-Join feature is enabled for the given SSID.

    :param str name: The name of the SSID.

    :return: ``True`` if enabled, ``False`` if disabled or not available.

    :rtype: bool

    CLI Example:

    .. code-block:: bash

        salt '*' wifi.autojoin_enabled PiedPiper
    '''
    if not __salt__['wifi.exists'](name):
        return False

    return not __salt__['wifi.autojoin_disabled'](name)


def current_ssid():
    '''
    Get the current SSID that WiFi is connected to.

    :return: Name of the current SSID.

    :rtype: str

    CLI Example:

    .. code-block:: bash

        salt '*' wifi.current_ssid
    '''
    cmd = '/usr/sbin/networksetup -getairportnetwork en0'
    try:
        return __salt__['cmd.run'](cmd).split(':')[1].lstrip().rstrip()
    except (CommandExecutionError, IndexError) as err:
        log.trace('Caught Error: {}'.format(err))
        return None
