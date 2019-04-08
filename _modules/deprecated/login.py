'''
Login Module
============

Handle login preferences and items for Mac OS X.

TODO:
- Should list mechanisms attached to the loginwindow via the auth db, as a part of the `system.login.console`
authorization right.

:maintainer:    Mosen <mosen@github.com>
:maturity:      new
:depends:       objc,LaunchServices
:platform:      darwin
'''

import logging
import salt.utils

HAS_LIBS = False
try:
    import objc
    # from LaunchServices import LSSharedFileListCreate, \
    #     kLSSharedFileListSessionLoginItems, \
    #     kLSSharedFileListGlobalLoginItems, \
    #     LSSharedFileListRef, \
    #     LSSharedFileListCopySnapshot, \
    #     LSSharedFileListItemCopyDisplayName

    from Foundation import NSBundle

    HAS_LIBS = True
except ImportError:
    pass

__virtualname__ = 'login'


def __virtual__():
    '''
    Only load if the platform is correct and we can use PyObjC libs
    '''
    if not salt.utils.platform.is_darwin():
        log.warning('Cant load OS X login module because platform is not Darwin')
        return False

    if not HAS_LIBS:
        log.warning('Cant load OS X login module because could not import functions')
        return False

    return __virtualname__


log = logging.getLogger(__name__)  # Start logging


# Deprecated in 10.11
# In the user context, LSSharedFileListCreate() gets the root list because salt runs under sudo
# def items(context):
#     '''
#     Get a list of 'Login Items'
#
#     context
#         The shared file list context: 'user' (meaning the current session) or 'system'.
#         The default login item list will be the 'system' list.
#
#     CLI Example:
#
#     .. code-block:: bash
#
#         salt '*' login.items [context]
#     '''
#     if context == 'user':
#         defined_context = kLSSharedFileListSessionLoginItems
#     else:
#         defined_context = kLSSharedFileListGlobalLoginItems
#
#     log.info('Getting login items for the %s context', 'user' if context == 'user' else 'system')
#     lst = LSSharedFileListCreate(None, defined_context, None)
#     snapshot, seed = LSSharedFileListCopySnapshot(lst, None)  # snapshot is CFArray
#
#     log.info('Login item display names:')
#     login_items = [LSSharedFileListItemCopyDisplayName(item) for item in snapshot]
#     log.info(login_items)
#
#     return login_items


def hidden_users():
    '''
    Get a list of users hidden from the login window

    CLI Example:

    .. code-block:: bash

        salt '*' login.hidden_users
    '''
    users = __salt__['plist.read_key']('/Library/Preferences/com.apple.loginwindow.plist', 'HiddenUsersList')
    return [str(user) for user in users]


def picture():
    '''
    Get the path of the picture shown in the background of loginwindow (if any)

    CLI Example:

    .. code-block:: bash

        salt '*' login.picture
    '''
    __salt__['plist.read_key']('/Library/Preferences/com.apple.loginwindow.plist', 'DesktopPicture')


def set_picture(path):
    '''
    Set the background of the loginwindow to the given path

    CLI Example:

    .. code-block:: bash

        salt '*' login.set_picture /path/to/desktop.jpg
    '''
    __salt__['plist.write_key']('/Library/Preferences/com.apple.loginwindow.plist', 'DesktopPicture', 'string', path)
    # TODO: kill loginwindow if already at the loginwindow?


def text():
    '''
    Get the text to be displayed at the bottom of the loginwindow (if any)

    CLI Example:

    .. code-block:: bash

        salt '*' login.text
    '''
    __salt__['plist.read_key']('/Library/Preferences/com.apple.loginwindow.plist', 'LoginwindowText')


def set_text(value):
    '''
    Set some text to be displayed at the bottom of the Login window

    CLI Example:

    .. code-block:: bash

        salt '*' login.text 'Unauthorized access prohibited'
    '''
    __salt__['plist.write_key']('/Library/Preferences/com.apple.loginwindow.plist', 'LoginwindowText', 'string', value)
    # TODO: kill loginwindow if already at the loginwindow?


def auto_login():
    '''
    Get the enabled state of auto login, and the currently assigned user (if any)

    CLI Example:

    .. code-block:: bash

        salt '*' login.auto_login
    '''
    __salt__['plist.read_key']('/Library/Preferences/com.apple.loginwindow.plist', 'autoLoginUser')


def set_auto_login(enabled, username):
    '''
    Set the auto login state

    enabled
        Is auto login enabled? True/False

    username
        The user name to use for auto login

    CLI Example:

    .. code-block:: bash

        salt '*' login.set_auto_login <enabled> <username>
    '''
    if enabled:
        __salt__['plist.write_key']('/Library/Preferences/com.apple.loginwindow.plist', 'autoLoginUser', 'string', username)
        __salt__['plist.write_key']('/Library/Preferences/.GlobalPreferences', 'com.apple.userspref.DisableAutoLogin', 'bool', True)
    else:
        __salt__['plist.delete_key']('/Library/Preferences/com.apple.loginwindow.plist', 'autoLoginUser')


def display_mode():
    '''
    Display login window as:
        - List of users = 'list'
        - Name and password = 'inputs'

    One of 'list' or 'inputs' is returned

    CLI Example:

    .. code-block:: bash

        salt '*' login.display_mode
    '''
    is_inputs_mode = __salt__['plist.read_key']('/Library/Preferences/com.apple.loginwindow.plist', 'SHOWFULLNAME')

    if is_inputs_mode:
        return 'inputs'
    else:
        return 'list'

def set_display_mode(mode):
    '''
    (Set) Display login window as:
        - List of users = 'list'
        - Name and password = 'inputs'

    CLI Example:

    .. code-block:: bash

        salt '*' login.set_display_mode <inputs|list>
    '''
    if mode not in ['inputs', 'list']:
        # no valid mode given
        return False
    else:
        is_inputs_mode = True if mode == 'inputs' else False
        __salt__['plist.write_key']('/Library/Preferences/com.apple.loginwindow.plist', 'SHOWFULLNAME', 'bool', is_inputs_mode)
        return True

def display_power_buttons():
    '''
    Show the Sleep, Restart, and Shut Down buttons

    Returns true if this preference is enabled

    CLI Example:

    .. code-block:: bash

        salt '*' login.display_power_buttons
    '''
    is_buttons_hidden = __salt__['plist.read_key']('/Library/Preferences/com.apple.loginwindow.plist', 'PowerOffDisabled')
    return not is_buttons_hidden


def set_display_power_buttons(enabled):
    '''
    (Set) Show the Sleep, Restart, and Shut Down buttons

    CLI Example:

    .. code-block:: bash

        salt '*' login.set_display_power_buttons <true|false>
    '''
    is_buttons_hidden = True if enabled == 'false' else False
    __salt__['plist.write_key']('/Library/Preferences/com.apple.loginwindow.plist', 'PowerOffDisabled', 'bool', is_buttons_hidden)

def display_input_menu():
    pass # showInputMenu (BOOL)

def display_password_hints():
    pass # RetriesUntilHint (INT) default 3, off = 0


def users():
    '''
    Get a list of users logged in. This includes both the active console user and all other users logged in via fast
    switching.
    '''
    CG_bundle = NSBundle.bundleWithIdentifier_('com.apple.CoreGraphics')
    functions = [("CGSSessionCopyAllSessionProperties", b"@"),]
    objc.loadBundleFunctions(CG_bundle, globals(), functions)

    userlist = CGSSessionCopyAllSessionProperties()
    result = list()

    for user in userlist:
        result.append({
            'username': user['kCGSSessionUserNameKey'],
            'longname': user['kCGSessionLongUserNameKey'],
            'console': user['kCGSSessionOnConsoleKey'],
            'logged_in': user['kCGSessionLoginDoneKey']
        })

    return result
