'''
Login Module
============

Handle login preferences and items for Mac OS X.

TODO:
- Should list mechanisms attached to the loginwindow via the auth db, as a part of the `system.login.console`
authorization right.

:maintainer:    Mosen <mosen@github.com>
:maturity:      new
:depends:       objc, plist
:platform:      darwin
'''

from salt.utils.decorators import depends
import logging

HAS_LIBS = False
try:
    from LaunchServices import LSSharedFileListCreate, \
        kLSSharedFileListSessionLoginItems, \
        kLSSharedFileListGlobalLoginItems, \
        LSSharedFileListRef, \
        LSSharedFileListCopySnapshot, \
        LSSharedFileListItemCopyDisplayName

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


log = logging.getLogger(__name__)  # Start logging


def items(context):
    '''
    Get a list of 'Login Items'

    context
        The shared file list context: 'user' (meaning the current session) or 'system'.
        The default login item list will be the 'system' list.

    CLI Example:

    .. code-block:: bash

        salt '*' login.items [context]
    '''
    if context == 'user':
        defined_context = kLSSharedFileListSessionLoginItems
    else:
        defined_context = kLSSharedFileListGlobalLoginItems

    lst = LSSharedFileListCreate(None, defined_context, None)
    snapshot, seed = LSSharedFileListCopySnapshot(lst, None)  # snapshot is CFArray

    return [LSSharedFileListItemCopyDisplayName(item) for item in snapshot]


@depends('plist')
def hidden_users():
    '''
    Get a list of users hidden from the login window

    CLI Example:

    .. code-block:: bash

        salt '*' login.hidden_users
    '''
    users = __salt__['plist.read_key']('/Library/Preferences/com.apple.loginwindow.plist', 'HiddenUsersList')
    return [str(user) for user in users]


@depends('plist')
def picture(path):
    '''
    Set the background of the loginwindow to the given path

    CLI Example:

    .. code-block:: bash

        salt '*' login.picture /path/to/desktop.jpg
    '''
    __salt__['plist.write_key']('/Library/Preferences/com.apple.loginwindow.plist', 'DesktopPicture', 'string', path)
    # TODO: kill loginwindow if already at the loginwindow?


@depends('plist')
def text(value):
    '''
    Set some text to be displayed at the bottom of the Login window

    CLI Example:

    .. code-block:: bash

        salt '*' login.text 'Unauthorized access prohibited'
    '''
    __salt__['plist.write_key']('/Library/Preferences/com.apple.loginwindow.plist', 'LoginwindowText', 'string', value)
    # TODO: kill loginwindow if already at the loginwindow?