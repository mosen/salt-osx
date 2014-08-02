'''
Munki Module
============

Control munki client preferences.
Shortcuts for munki client checks.

:maintainer:    Mosen <mosen@github.com>
:maturity:      new
:depends:       objc,plist
:platform:      darwin
'''

import logging

__virtualname__ = 'munki'

def __virtual__():
    '''
    Only load if the platform is correct and we can use PyObjC libs
    '''
    if __grains__.get('kernel') != 'Darwin':
        return False

    return __virtualname__


log = logging.getLogger(__name__)  # Start logging

def clientid():
    '''
    Get the current munki ClientIdentifier

    CLI Example:

    .. code-block:: bash

        salt '*' munki.cid
    '''
    return __salt__['plist.read_key']('/Library/Preferences/ManagedInstalls.plist', 'ClientIdentifier')


def set_clientid(client_identifier):
    '''
    Set the current munki ClientIdentifier

    CLI Example:

    .. code-block:: bash

        salt '*' munki.set_cid 'developer'
    '''
    __salt__['plist.write_key']('/Library/Preferences/ManagedInstalls.plist', 'ClientIdentifier', 'string', client_identifier)

