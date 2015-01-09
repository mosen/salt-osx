# -*- coding: utf-8 -*-
'''
Alter property lists through the use of the NSUserDefaults API.
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

    from Foundation import NSUserDefaults, NSMutableDictionary

    HAS_LIBS = True
except ImportError:
    log.debug('Error importing dependencies for plist (NSUserDefaults) execution module.')

__virtualname__ = 'defaults'

def __virtual__():
    '''
    Only load if the platform is correct and we can use PyObjC libs
    '''
    if not salt.utils.is_darwin():
        return False

    if not HAS_LIBS:
        return False

    return __virtualname__

def read(bundle):
    '''
    Read the defaults for the given application bundle identifier.

    bundle
        A reverse-dns style name of the application bundle id to read.

    .. code-block:: bash

        salt '*' plist.read com.apple.Finder
    '''
    defaults = NSUserDefaults.standardUserDefaults()
    defaults.addSuiteNamed_(bundle)
    contents = defaults.dictionaryRepresentation()

    return contents
