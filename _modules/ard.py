# -*- coding: utf-8 -*-
'''
manage the "remote management" service via kickstart and property lists.

:maintainer:    Mosen <mosen@github.com>
:maturity:      beta
:depends:       plist
:platform:      darwin
'''
# This would not have been possible without the hard work from dayglojesus/managedmac

import binascii
import logging
import os

from salt.exceptions import CommandExecutionError
import salt.utils

log = logging.getLogger(__name__)

__virtualname__ = 'ard'

_PATHS = {
    'kickstart': '/System/Library/CoreServices/RemoteManagement/ARDAgent.app/Contents/Resources/kickstart',
    'dscl': '/usr/bin/dscl',
    'vnc_password': '/Library/Preferences/com.apple.VNCSettings.txt',
    'preferences': '/Library/Preferences/com.apple.RemoteManagement.plist',
    'trigger': '/private/etc/RemoteManagement.launchd'
}

# This number is used for basic XOR encryption by the VNC service.
_VNC_SEED = '1734516E8BA8C5E2FF1C39567390ADCA'

# Directly lifted from managedmac:
# Privileges are are represented using a signed integer stored as a
# string. Yes, confusing. Use this Bit map chart to figure it out:
#
# 64 Bit Hex Int Bit Decimal Checkbox Item
#    ================================================================
#    FFFFFFFFC0000000 0 -1073741824 enabled but nothing set
#    FFFFFFFFC0000001 1 -1073741823 send text msgs
#    FFFFFFFFC0000002 2 -1073741822 control and observe, show when observing
#    FFFFFFFFC0000004 3 -1073741820 copy items
#    FFFFFFFFC0000008 4 -1073741816 delete and replace items
#    FFFFFFFFC0000010 5 -1073741808 generate reports
#    FFFFFFFFC0000020 6 -1073741792 open and quit apps
#    FFFFFFFFC0000040 7 -1073741760 change settings
#    FFFFFFFFC0000080 8 -1073741696 restart and shutdown
#
#    FFFFFFFF80000002 -2147483646 control and observe don't show when observing
#    FFFFFFFFC00000FF -1073741569 all enabled
#    FFFFFFFF80000000 -2147483648 all disabled


# Mask out bytes that control whether the user is notified when observed.
_NAPRIV_HIDDEN_MASK = int('0x00000000FF000000', 16)

# Mask out bytes that are used to store privileges
_NAPRIV_PRIVS_MASK = int('0x00000000000000FF', 16)

# This is the base 64-bit integer used. Hidden attribute and privileges will be OR'ed to produce the final naprivs int.
_NAPRIV = int('0xFFFFFFFF00000000', 16)

# _NAPRIV_ENABLED_DISABLED = 0  # This can mean enabled or disabled when no privileges are set.
_NAPRIV_TEXT_MESSAGES = 1 << 0
_NAPRIV_CONTROL_OBSERVE = 1 << 1
_NAPRIV_COPY_ITEMS = 1 << 2
_NAPRIV_DELETE_REPLACE_ITEMS = 1 << 3
_NAPRIV_GENERATE_REPORTS = 1 << 4
_NAPRIV_OPEN_QUIT_APPS = 1 << 5
_NAPRIV_CHANGE_SETTINGS = 1 << 6
_NAPRIV_RESTART_SHUTDOWN = 1 << 7
_NAPRIV_ALL = _NAPRIV_TEXT_MESSAGES | _NAPRIV_CONTROL_OBSERVE | _NAPRIV_COPY_ITEMS \
              | _NAPRIV_DELETE_REPLACE_ITEMS | _NAPRIV_GENERATE_REPORTS | _NAPRIV_OPEN_QUIT_APPS | \
              _NAPRIV_CHANGE_SETTINGS | _NAPRIV_RESTART_SHUTDOWN

_NAPRIVS = {
    'text': _NAPRIV_TEXT_MESSAGES,
    'control_observe': _NAPRIV_CONTROL_OBSERVE,
    'copy': _NAPRIV_COPY_ITEMS,
    'delete_replace': _NAPRIV_DELETE_REPLACE_ITEMS,
    'reports': _NAPRIV_GENERATE_REPORTS,
    'launch': _NAPRIV_OPEN_QUIT_APPS,
    'settings': _NAPRIV_CHANGE_SETTINGS,
    'restart_shutdown': _NAPRIV_RESTART_SHUTDOWN
}

_NAPRIVS_FLIP = {y: x for x, y in _NAPRIVS.items()}


def __virtual__():
    '''
    Only load module if we are running on OS X.
    '''
    return __virtualname__ if salt.utils.platform.is_darwin() else False


def _xorhexs(xor, value):
    '''
    Generate XORed string value.
    Read in hex number as string, convert to bytes and xor against each other.
    '''
    if not value:
        value = ''

    xor_list = [int(h + l, 16) for (h, l) in zip(xor[0::2], xor[1::2])]
    value_list = [int(h + l, 16) for (h, l) in zip(value[0::2], value[1::2])]

    def reduce_xor(memo, c):
        '''reduce by XORing and substituting with NUL when out of bounds'''
        v = value_list.pop(0) if len(value_list) > 0 else 0
        return memo + chr(c ^ v)

    result = reduce(reduce_xor, xor_list, '')
    return result


def _is_notified(naprivs):
    '''
    Given a signed integer of remote management privileges, determine whether the user will be notified (when screen
    is being observed).
    '''
    # 0xC0 - User is notified of control / User access is enabled if privs are nothing.
    # 0x80 - User will not be notified / User access is disabled if privs are nothing.
    # Take highest byte and bit shift down to compare against 0xC0/0x80
    notify_byte = (naprivs & _NAPRIV_HIDDEN_MASK) >> 24
    return True if notify_byte & int('0xC0', 16) == int('0xC0', 16) else False


def _naprivs_to_list(naprivs):
    '''
    Convert a signed integer representation of remote management privileges to
    a list of short words indicating the permissions set.

    If the 'all' privilege is set, only returns 'all'
    '''
    if naprivs & _NAPRIV_ALL == _NAPRIV_ALL:
        privs = ['all']
    else:
        privs = [k for k, v in _NAPRIVS.items() if naprivs & v == v]

    if _is_notified(naprivs):
        privs.append('observe_notified')
    else:
        privs.append('observe_hidden')

    return privs


def _list_to_naprivs(privs):
    '''
    Convert a list of short words to a signed integer representing those remote management privileges.

    If you specify that a user has 'all' privilege, all other privileges in the set are discarded.

    If 'observe_hidden' or 'observe_notified' are not contained within the set, we will assume that the observe
    privilege will come without user notification.
    '''
    if 'all' in privs:
        valid_privs = ['all']
        napriv_privs = _NAPRIV_ALL
    else:
        valid_privs = [priv for priv in privs if priv in _NAPRIVS]
        napriv_privs = reduce(lambda x, y: x | y, [_NAPRIVS[valid_priv] for valid_priv in valid_privs])

    if 'observe_notified' in privs:
        notify_byte = int('0xC0', 16) << 24  # Observation Notified
    else:
        notify_byte = int('0x80', 16) << 24  # Observation Hidden

    naprivs = _NAPRIV | notify_byte | napriv_privs
    naprivs_twos = ~(int('0xFFFFFFFFFFFFFFFF', 16) - naprivs)

    return naprivs_twos


def active():
    '''
    Determine whether the remote management service is active.

    CLI Example:

    .. code-block:: bash

        salt '*' ard.active
    '''
    # TODO: OSX netstat implementation for salt.modules.netstat

    # VNC Port 5900
    # if not __salt__['cmd.retcode']('/usr/sbin/netstat |grep .rfb') == 0:
    #     log.debug('Not listening on tcp 5900 (vnc)')
    #     return False

    # Remote Management Port 3283
    # if not __salt__['cmd.retcode']('/usr/sbin/netstat |grep .net-assistant') == 0:
    #     log.debug('Not listening on tcp 3283 (remote desktop)')
    #     return False

    # Is the trigger file present?
    if not os.path.isfile(_PATHS['trigger']):
        log.debug('Remote Management trigger file: {0} does not exist.'.format(_PATHS['trigger']))
        return False

    # Is the ARDAgent process running?
    # TODO: OSX implementation ps.pgrep
    if not __salt__['cmd.retcode']('ps axc | grep ARDAgent > /dev/null', python_shell=False) == 0:
        log.debug('ARDAgent process is not running.')
        return False

    return True


def activate():
    '''
    Activate the remote management service.

    CLI Example:

    .. code-block:: bash

        salt '*' ard.activate
    '''
    kickstart = _PATHS['kickstart']
    output = __salt__['cmd.run']('{0} -activate'.format(kickstart))

    return output


def deactivate():
    '''
    Deactivate (and stop) the remote management service.

    CLI Example:

    .. code-block:: bash

        salt '*' ard.deactivate
    '''
    kickstart = _PATHS['kickstart']
    output = __salt__['cmd.run']('{0} -deactivate -stop'.format(kickstart))

    return output


def vncpw():
    '''
    Retrieve the current VNC password.

    CLI Example:

    .. code-block:: bash

        salt '*' ard.vncpw
    '''
    passwordPath = _PATHS['vnc_password']

    if not os.path.isfile(passwordPath):
        return None

    f = open(passwordPath, 'r')

    try:
        crypted_string = f.read()
        password = _xorhexs(_VNC_SEED, crypted_string).strip("\x00")  # XOR and strip NULs
    finally:
        f.close()

    return password


def set_vncpw(password=None):
    '''
    Set the current VNC password.

    password
        The password to set. If empty, the current password will be removed.

    CLI Example:

    .. code-block:: bash

        salt '*' ard.set_vncpw password
    '''
    if password is None and os.path.isfile(_PATHS['vnc_password']):
        os.unlink(_PATHS['vnc_password'])

    hex_password = binascii.hexlify(password) if password else None
    crypted = _xorhexs(_VNC_SEED, hex_password)

    f = open(_PATHS['vnc_password'], 'w')

    try:
        f.write(binascii.hexlify(crypted))
    finally:
        f.close()

    return True


def user_privs(username, human=True):
    '''
    Retrieve remote management privileges for a single user.
    Returns a dictionary with username as key, and list of privileges as the value.

    This may return false if the username was not found, or none if the user exists but the privileges
    attribute doesn't exist (no privileges).

    username
        Exact local login name

    human : True
        Whether the signed integer privilege should be converted to a readable short string.

    CLI Example:

    .. code-block:: bash

        salt '*' ard.user_privs admin
    '''
    privs = __salt__['dscl.read']('.', '/Users/{0}'.format(username), 'naprivs')

    if privs is False or privs is None or len(privs.values()) == 0:
        return None

    log.debug('Got naprivs: {}'.format(privs))

    privs_long = int(privs.values()[0])

    if human:
        return {username: _naprivs_to_list(privs_long)}
    else:
        return {username: privs_long}


def users(human=True):
    '''
    Get a list of users with their privileges to remote management.
    Returns a list of dictionaries with username as key, and list of privileges as the value.

    human : True
        Whether the signed integer privilege should be converted to a readable short string.

    CLI Example:

    .. code-block:: bash

        salt '*' ard.users
    '''
    privs = __salt__['dscl.list']('.', '/Users', 'naprivs')
    log.debug('Current remote desktop privileges: {}'.format(privs))

    if not human:
        return privs

    privs_human = {user: _naprivs_to_list(int(privs)) for user, privs in privs.items()}
    return privs_human


def set_user_privs(username, privileges):
    '''
    Set user remote management privileges.

    username
        Valid system user.

    privileges
        Remote management privileges. A comma delimited string containing privileges in the short form listed below.
        The ``all`` privilege can be used instead of combining every privilege.

        If you do not specify whether the user will be notified when they are being observed, the default is NOT to
        notify the user.

        Valid privilege names:
        - ``enabled`` enabled but nothing set
        - ``text`` send text msgs
        - ``control_observe`` control and observe
        - ``copy`` copy items
        - ``delete_replace`` delete and replace items
        - ``reports`` generate reports
        - ``launch`` open and quit apps
        - ``settings`` change settings
        - ``restart_shutdown`` restart and shutdown
        - ``all`` all enabled
        - ``disabled`` all disabled

        Special privilege to modify user notification when a user is observed:
        - ``observe_notified`` notify user when being observed.
        - ``observe_hidden`` (default) user is not notified.

    CLI Example:

    .. code-block:: bash

        salt '*' ard.user_privs admin settings,launch,copy
    '''
    if __salt__['dscl.search']('/Search', '/Users', 'name', username) is None:
        log.warning(
            'Cannot set remote management privileges for user: {0}, user was not found in the directory search path.'.format(
                username))
        return False

    naprivs = privileges.split(',')
    napriv_long = _list_to_naprivs(naprivs)

    success = __salt__['dscl.create']('.', '/Users/{0}'.format(username), 'naprivs', napriv_long)
    return success


def naprivs_list(naprivs):
    '''
    (Internal use) Convert a signed integer of naprivs to a python list of short words representing
    those privileges.

    naprivs
        Signed int representing remote management privileges

    CLI Example:

    .. code-block:: bash

        salt '*' ard.naprivs_list -1073741824
    '''
    return _naprivs_to_list(int(naprivs))


def list_naprivs(privs):
    '''
    (Internal use) Convert a comma delimited list of shortname privileges to a signed integer
    representation for the remote management service.

    privs
        Comma delimited short names of privileges, no spaces.

    CLI Example:

    .. code-block:: bash

        salt '*' ard.list_naprivs all,observe_hidden
    '''
    return _list_to_naprivs(privs.split(','))
