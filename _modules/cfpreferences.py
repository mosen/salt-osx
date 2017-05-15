# -*- coding: utf-8 -*-
"""
Alter property lists through the use of the CFPreferences API.
(Just testing the possibility of using this API)

:maintainer:    Mosen <mosen@github.com>
:maturity:      new
:depends:       objc
:platform:      darwin
"""

import logging
import salt.utils

log = logging.getLogger(__name__)  # Start logging

HAS_LIBS = False
try:
    from CoreFoundation import CFGetTypeID, \
        CFPreferencesCopyValue, \
        CFPreferencesSetValue, \
        CFPreferencesSynchronize, \
        CFPreferencesCopyMultiple, \
        CFPreferencesCopyKeyList, \
        kCFPreferencesAnyUser, \
        kCFPreferencesAnyHost, \
        kCFPreferencesCurrentUser, \
        kCFPreferencesCurrentHost

    HAS_LIBS = True
except ImportError:
    log.debug('Error importing dependencies for CFPreferences execution module.')

__virtualname__ = 'cfpreferences'

def __virtual__():
    """
    Only load if the platform is correct and we can use PyObjC libs
    """
    if not salt.utils.is_darwin():
        return False

    if not HAS_LIBS:
        return False

    return __virtualname__


def read(appid, key, byHost=True):
    """
    Get the preference value for an Application ID and requested key.

    appid
        Bundle identifier such as com.apple.Finder

    key
        Preference key to read

    .. code-block:: bash

        salt '*' cfpreferences.read com.apple.Finder NSNavLastRootDirectory
    """
    host = kCFPreferencesCurrentHost if byHost else kCFPreferencesAnyHost
    value = CFPreferencesCopyValue(key, appid, kCFPreferencesAnyUser, host)

    valueType = CFGetTypeID(value)

    from pprint import pprint
    pprint(valueType)

    return value


def write(appid, key, value, byHost=True):
    """
    Write a simple preference value.

    appid
        Bundle identifier such as com.apple.Finder

    key
        Preference key to read

    .. code-block:: bash

        salt '*' cfpreferences.write com.example.test example a

    """
    host = kCFPreferencesCurrentHost if byHost else kCFPreferencesAnyHost

    CFPreferencesSetValue(key, value, appid, kCFPreferencesAnyUser, host)
    didSync = CFPreferencesSynchronize(appid, kCFPreferencesAnyUser, host)
    return didSync


def keys(appid, byHost=True):
    """
    Read a list of keys available

    appid
        Bundle identifier such as com.apple.Finder
    """
    host = kCFPreferencesCurrentHost if byHost else kCFPreferencesAnyHost

    keyList = CFPreferencesCopyKeyList(appid, kCFPreferencesAnyUser, host)
    if keyList is None:
        return None
    else:
        return list(keyList)
