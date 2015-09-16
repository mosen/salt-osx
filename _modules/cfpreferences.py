# -*- coding: utf-8 -*-
'''
Alter property lists through the use of the CFPreferences API.
(Just testing the possibility of using this API)

:maintainer:    Mosen <mosen@github.com>
:maturity:      new
:depends:       objc
:platform:      darwin
'''

import logging
import salt.utils

log = logging.getLogger(__name__)  # Start logging

HAS_LIBS = False
try:
    from Foundation import CFPreferencesCopyValue, \
        CFPreferencesSetValue, \
        CFPreferencesSynchronize, \
        kCFPreferencesAnyUser, \
        kCFPreferencesAnyHost

    HAS_LIBS = True
except ImportError:
    log.debug('Error importing dependencies for CFPreferences execution module.')

__virtualname__ = 'cfpreferences'

def __virtual__():
    '''
    Only load if the platform is correct and we can use PyObjC libs
    '''
    if not salt.utils.is_darwin():
        return False

    if not HAS_LIBS:
        return False

    return __virtualname__


def read(appid, key, byhost=False):
    '''
    Get the preference value for an Application ID and requested key.

    appid
        Bundle identifier such as com.apple.Finder

    key
        Preference key to read

    byhost : False
        Whether the preference is for the current host

    .. code-block:: bash

        salt '*' cfpreferences.read com.apple.Finder NSNavLastRootDirectory
    '''
    value = CFPreferencesCopyValue(key, appid, kCFPreferencesAnyUser, kCFPreferencesAnyHost)
    return value


def write(appid, key, value, byhost=False):
    '''
    Write a simple preference value.

    appid
        Bundle identifier such as com.apple.Finder

    key
        Preference key to read

    byhost : False
        Whether the preference is for the current host

    .. code-block:: bash

        salt '*' cfpreferences.write com.example.test example a

    '''
    didSync = CFPreferencesSynchronize(appid, kCFPreferencesAnyUser, kCFPreferencesAnyHost)
    CFPreferencesSetValue(key, value, appid, kCFPreferencesAnyUser, kCFPreferencesAnyHost)
    didSync = CFPreferencesSynchronize(appid, kCFPreferencesAnyUser, kCFPreferencesAnyHost)
    return didSync