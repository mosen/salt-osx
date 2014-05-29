'''
Login Module
============

Handle login preferences and items for Mac OS X.

:maintainer:    Mosen <mosen@github.com>
:maturity:      new
:depends:       objc
:platform:      darwin
'''

import logging
import objc

HAS_LIBS = False
try:
    from ApplicationServices import LSSharedFileListCreate, \
        kLSSharedFileListSessionLoginItems, \
        kLSSharedFileListGlobalLoginItems, \
        LSSharedFileListRef

    HAS_LIBS = True
except ImportError:
    pass

__virtualname__ = 'login'


def __virtual__():
    '''
    Only load if the platform is correct and we can use PyObjC libs
    '''
    if __grains__.get('kernel') != 'Darwin':
        return False

    if not HAS_LIBS:
        return False

    return __virtualname__

def items(context):
    '''
    Get a list of 'Login Items'

    context
        The shared file list context: 'user' (meaning the current session) or 'system'

    CLI Example:

    .. code-block:: bash

        salt '*' login.items [context]
    '''
    if context == 'user':
        defined_context = kLSSharedFileListSessionLoginItems
    else:
        defined_context = kLSSharedFileListGlobalLoginItems

    loginItems = LSSharedFileListCreate(objc.NULL, defined_context, objc.NULL)

    for item in loginItems:
        pass


def hidden_users():
    '''
    Get a list of users hidden from the login window

    CLI Example:

    .. code-block:: bash

        salt '*' login.hidden_users
    '''

