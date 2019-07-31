# -*- coding: utf-8 -*-
'''
Support for reading and writing of preference key/values with ObjectiveC's CFPreferences
Modules. Documentation on the Modules can be found here. https://developer.apple.com/documentation/corefoundation/preferences_utilities?language=objc

This appears to be significantly faster than shelling out to `defaults`.

This module has some caveats.
1. Requires the PyObjC package. It will try to import this package from Salts
path, if that fails it will try to use the system PyObjC that ships with macOS.
'''
# py libs
import logging
import sys
import os
import pwd
# salt libs
import salt.utils
import salt.utils.platform
from salt.exceptions import CommandExecutionError

log = logging.getLogger(__name__)

try:
    import Foundation
    from PyObjCTools import Conversion
    log.trace('module.mac_prefs - PyObjC import successful.')
except ImportError:
    log.trace('module.mac_prefs - Failed to Import PyObjC, Using Sys.')
    sys.path.append('/System/Library/Frameworks/Python.framework/Versions/2.7/Extras/lib/python/PyObjC')
    import Foundation
    from PyObjCTools import Conversion


__virtualname__ = 'prefs'

__func_alias__ = {
    'set_': 'set',
    'list_': 'list',
}

def __virtual__():
    if salt.utils.platform.is_darwin():
        return __virtualname__

    return (False, 'module.mac_prefs only available on macOS.')


def _convert_pyobjc_objects(pref):
    '''
    Types get returned as ObjectiveC classes from PyObjC and salt has a hard time
    writing those out, so this function will convert NSDictionary and NSArray
    object to normal list and dictionary python objects.
    '''
    if isinstance(pref, Foundation.NSDate):
        log.debug('mac_prefs._convert_pyobjc_objects - '
                  'converting "{}" NSDate to string...'.format(pref))
        return str(pref)

    return Conversion.pythonCollectionFromPropertyList(pref)


def _get_user_and_host(user, host):
    '''
    returns a tuple of kCFPreferences(Any/Current)User and
    kCFPreferences(Any/Current)Host.
    '''
    if user.lower() == 'any':
        user_pref = Foundation.kCFPreferencesAnyUser
    elif user.lower() == 'current':
        user_pref = Foundation.kCFPreferencesCurrentUser
    else:
        raise CommandExecutionError(
            'Error proccessing parameter "user": [{0}], must be "any" or'
            ' "current". NOT [{0}]'.format(user)
        )

    if host.lower() == 'any':
        host_pref = Foundation.kCFPreferencesAnyHost
    elif host.lower() == 'current':
        host_pref = Foundation.kCFPreferencesCurrentHost
    else:
        raise CommandExecutionError(
            'Error proccessing parameter "host": [{0}], must be "any" or'
            ' "current". NOT [{0}]'.format(host)
        )
    log.debug('Using user domain: [{}] and host domain: [{}]'.format(user_pref,
                                                                     host_pref))
    return (user_pref, host_pref)


def _read_pref(name, domain, user, host, runas):
    '''
    helper function for reading the preference, either at the user level
    or system level
    '''
    if runas:
        try:
            # convert to uid for later use.
            uid = pwd.getpwnam(runas).pw_uid
        except KeyError:
            raise CommandExecutionError(
                'Set to runas user {}, this user'
                ' does not exist.'.format(runas)
            )
        # need to run as the user
        log.debug('Setting EUID to {}'.format(runas))
        os.seteuid(uid)

    if user:
        user_domain, host_domain = _get_user_and_host(user, host)
        log.debug('Reading key: "{}" in domain: "{}"'.format(name, domain))
        value = Foundation.CFPreferencesCopyValue(name,
                                                  domain,
                                                  user_domain,
                                                  host_domain)
        os.seteuid(0)
        return value

    #need to bring ourselves back up to root
    path = '/var/root/Library/Preferences/'
    d_path = os.path.join(path, domain)
    log.debug('Reading key: "{}" in domain: "{}" at "{}"'.format(name, domain, d_path))
    return Foundation.CFPreferencesCopyAppValue(name, domain)


def _set_pref(name, value, domain, user, host, runas):
    '''
    sets the pref for the user not at the app value level
    returns true or false if the preference was set correctly or not.
    '''
    if runas:
        try:
            # convert to uid for later use.
            uid = pwd.getpwnam(runas).pw_uid
        except KeyError:
            raise CommandExecutionError(
                'Set to runas user {}, this user'
                ' does not exist.'.format(runas)
            )
        # need to run as the user
        log.debug('Setting EUID to {}'.format(runas))
        os.seteuid(uid)
    if user:
        pref_user, pref_host = _get_user_and_host(user, host)
        path = '/Library/Preferences/'
        d_path = os.path.join(path, domain)
        log.debug('Settting key: "{}" to value: "{}" in '
                  'domain: "{}" in "{}"'.format(name, value, domain, d_path))
        try:
            set_val = Foundation.CFPreferencesSetValue(name,
                                                       value,
                                                       domain,
                                                       pref_user,
                                                       pref_host)
            Foundation.CFPreferencesAppSynchronize(domain)
            os.seteuid(0)
            return set_val
        except BaseException:
            log.warning('prefs._set_pref caught exception on user set.')
            return False
    path = '/var/root/Library/Preferences/'
    d_path = os.path.join(path, domain)
    log.debug('Settting key: "{}" to value: "{}" in'
              ' domain: "{}" in "{}"'.format(name, value, domain, d_path))
    Foundation.CFPreferencesSetAppValue(name, value, domain)
    return Foundation.CFPreferencesAppSynchronize(domain)

def read(name, domain, user=None, host=None, runas=None):
    '''
    Read a preference using CFPreferences.

    name
        The preference key to read.

    domain
        The domain to in which the key should be read.

    user
        The user domain to use, either 'current' or 'any'

    host
        The host domain to use, either 'current' or 'any'

    runas
        The user to run as should be a short username.

    :return: The value of the key, or None if it doesn't exist.

    CLI Example:

    .. code-block:: bash

        salt '*' prefs.read IdleTime com.apple.ScreenSaver
        salt '*' prefs.read IdleTime com.apple.ScreenSaver True
    '''
    if (runas and not host) or (runas and not user)\
        or (runas and not user and not host):
        raise CommandExecutionError(
            'If using "runas" you must specify a "user" and "host" domains.'
        )
    if user and not host or host and not user:
        raise CommandExecutionError(
            'If using "host" or "user" you must specify both not just one.'
        )

    return _convert_pyobjc_objects(_read_pref(name,
                                              domain,
                                              user,
                                              host,
                                              runas))


def set_(name, value, domain, user=None, host=None, runas=None):
    '''
    Set a preference value using CFPreferences.

    name
        The preference key to set.

    value
        The value to which the key should be set. If you want to delete or
        remove the key set this parameter to None.

    domain
        The domain to which the key and value should be set in.

    user
        The user domain to use, either 'current' or 'any'

    host
        The host domain to use, either 'current' or 'any'

    runas
        The user to run as should be a short username.

    :return: A Boolean on whether or not the preference was set correctly.

    :rtype: bool

    CLI Example:

    .. code-block:: bash

        salt '*' prefs.set IdleTime 180 com.apple.ScreenSaver
        salt '*' prefs.set IdleTime 180 com.apple.ScreenSaver True
    '''
    if (runas and not host) or (runas and not user)\
        or (runas and not user and not host):
        raise CommandExecutionError(
            'If using "runas" you must specify a "user" and "host" domains.'
        )
    if user and not host or host and not user:
        raise CommandExecutionError(
            'If using "host" or "user" you must specify both not just one.'
        )
    set_val = _set_pref(name, value, domain, user, host, runas)

    # get the value to check if it was set correctly.
    new_val = read(name, domain, user, host, runas)

    log.debug('New value for key: "{}" in domain: '
              '"{}" is "{}"'.format(name, domain, new_val))

    # check to see if everything was set correctly
    if new_val != value:
        log.debug('prefs.set Value of {}, for key {}, '
                  'was not set properly.'.format(value, name))
        return False

    return True

def list_(name, user, host, runas=None, values=False):
    '''
    List all Keys in the given domain.

    name
        The preference domain to get keys from.

    user
        The user domain to use, either 'current' or 'any'

    host
        The host domain to use, either 'current' or 'any'

    runas
        The user to run as should be a short username.

    values
        Pass true to return a dictionary of the key value pairs.

    :rtype: list,dict

    CLI Example:

    .. code-block:: bash

        salt '*' prefs.list com.apple.RemoteManagement any any values=True
        salt '*' prefs.list com.apple.ScreenSaver current current runas=deadb33f
    '''

    log.debug('Gathering Key List for {}'.format(name))
    if (runas and not host) or (runas and not user)\
        or (runas and not user and not host):
        raise CommandExecutionError(
            'If using "runas" you must specify a "user" and "host" domains.'
        )
    if user and not host or host and not user:
        raise CommandExecutionError(
            'If using "host" or "user" you must specify both not just one.'
        )
    user_domain, host_domain = _get_user_and_host(user, host)
    if runas:
        try:
            # convert to uid for later use.
            uid = pwd.getpwnam(runas).pw_uid
        except KeyError:
            raise CommandExecutionError(
                'Set to runas user [{}], this user'
                ' does not exist.'.format(runas)
            )
        # need to run as the user
        log.debug('Setting EUID to [{}]'.format(runas))
        os.seteuid(uid)
    key_list = Foundation.CFPreferencesCopyKeyList(name, user_domain, host_domain)
    os.seteuid(0)
    con_key_list = _convert_pyobjc_objects(key_list) or []
    log.debug('Key list: "{}"'.format(con_key_list))
    if not values:
        return con_key_list

    value_dict = dict()

    try:
        for item in con_key_list:
            value_dict[item] = read(item, name, user, host, runas)
    except TypeError as exception:
        return None

    log.debug('Values List: "{}"'.format(value_dict))

    return value_dict
