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
    import os
    import ctypes

    from .CoreFoundation import CFPreferencesCopyAppValue

    HAS_LIBS = True
except ImportError:
    log.debug('Error importing dependencies for plist (CFPreferences) execution module.')

__virtualname__ = 'cfprefs'

def __virtual__():
    '''
    Only load if the platform is correct and we can use PyObjC libs
    '''
    if not salt.utils.is_darwin():
        return False

    if not HAS_LIBS:
        return False

    return __virtualname__

def read(path):
    '''
    Read the preferences for a given property list.

    path
        Full path to property list.

    .. code-block:: bash

        salt '*' cfprefs.read com.apple.Finder
    '''
    v = CFPreferencesCopyAppValue("NSNavLastRootDirectory", "com.apple.Terminal")

    return v
