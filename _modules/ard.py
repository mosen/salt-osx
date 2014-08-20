# -*- coding: utf-8 -*-
'''
manage the "remote management" service via kickstart and property lists.
'''
# This would not have been possible without the hard work from dayglojesus/managedmac

import os
import logging
import binascii
import salt.utils
from salt.exceptions import CommandExecutionError

log = logging.getLogger(__name__)

__virtualname__ = 'ard'

_PATHS = {
    'kickstart':'/System/Library/CoreServices/RemoteManagement/ARDAgent.app/Contents/Resources/kickstart',
    'dscl':'/usr/bin/dscl',
    'vnc_password':'/Library/Preferences/com.apple.VNCSettings.txt',
    'preferences':'/Library/Preferences/com.apple.RemoteManagement.plist',
    'trigger':'/private/etc/RemoteManagement.launchd'
}

# managedmac author has this to say:

# Privileges are are represented using a signed integer stored as a
# string. Yes, confusing. Use this Bit map chart to figure it out:
#
#    64 Bit Hex Int Bit Decimal Checkbox Item
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

_NAPRIV = int('0xFFFFFFFFC0000000',16)
_NAPRIV_NO_OBSERVE = int('0xFFFFFFFF80000000',16)

_NAPRIV_ENABLED = _NAPRIV
_NAPRIV_TEXT_MESSAGES = _NAPRIV + (1 << 0)
_NAPRIV_CONTROL_OBSERVE_NOTIFIED = _NAPRIV + (1 << 1)
_NAPRIV_COPY_ITEMS = _NAPRIV + (1 << 2)
_NAPRIV_DELETE_REPLACE_ITEMS = _NAPRIV + (1 << 3)
_NAPRIV_GENERATE_REPORTS = _NAPRIV + (1 << 4)
_NAPRIV_OPEN_QUIT_APPS = _NAPRIV + (1 << 5)
_NAPRIV_CHANGE_SETTINGS = _NAPRIV + (1 << 6)
_NAPRIV_RESTART_SHUTDOWN = _NAPRIV + (1 << 7)
_NAPRIV_ALL = _NAPRIV_ENABLED | _NAPRIV_TEXT_MESSAGES | _NAPRIV_CONTROL_OBSERVE_NOTIFIED | _NAPRIV_COPY_ITEMS \
              | _NAPRIV_DELETE_REPLACE_ITEMS | _NAPRIV_GENERATE_REPORTS | _NAPRIV_OPEN_QUIT_APPS | _NAPRIV_CHANGE_SETTINGS \
              | _NAPRIV_RESTART_SHUTDOWN


_NAPRIVS = {  # naprivs borrowed from managedmac
   'enabled': _NAPRIV_ENABLED,
   'text': _NAPRIV_TEXT_MESSAGES,
   'control_notified': _NAPRIV_CONTROL_OBSERVE_NOTIFIED,
#   'control_hidden': '-2147483646',
   'copy': _NAPRIV_COPY_ITEMS,
   'delete_replace': _NAPRIV_DELETE_REPLACE_ITEMS,
   'reports': _NAPRIV_GENERATE_REPORTS,
   'launch': _NAPRIV_OPEN_QUIT_APPS,
   'settings': _NAPRIV_CHANGE_SETTINGS,
   'restart_shutdown': _NAPRIV_RESTART_SHUTDOWN,
   'all': _NAPRIV_ALL
#   'disabled': '-2147483648'
}

_NAPRIVS_FLIP = {y:x for x,y in _NAPRIVS.iteritems()}

_VNC_SEED = '1734516E8BA8C5E2FF1C39567390ADCA'

def __virtual__():
    '''
    Only load module if we are running on OS X.
    '''
    return __virtualname__ if salt.utils.is_darwin() else False


def _xorhexs(xor, value):
    '''
    Generate XORed string value.
    Read in hex number as string, convert to bytes and xor against each other.
    '''
    if not value:
        value = ''

    xor_list = [int(h+l, 16) for (h,l) in zip(xor[0::2], xor[1::2])]
    value_list = [int(h+l, 16) for (h,l) in zip(value[0::2], value[1::2])]

    def reduce_xor(memo, c):
        '''reduce by XORing and substituting with NUL when out of bounds'''
        v = value_list.pop(0) if len(value_list) > 0 else 0
        return memo + chr(c^v)

    result = reduce(reduce_xor, xor_list, '')
    return result


def _privs_list(naprivs):
    '''
    Convert a signed integer representation of remote management privileges to
    a list of short words indicating the permissions set.
    '''
    return [k for k,v in _NAPRIVS.iteritems() if naprivs & v == v]

def _validate_user(name):
    output = __salt__['cmd.run']('/usr/bin/dscl /Search -search /Users name "{}"'.format(name))
    pass

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
    if not __salt__['cmd.retcode']('ps axc | grep ARDAgent > /dev/null') == 0:
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
        # Password is just XORed, implementation borrowed from dayglojesus/managedmac
        crypted_string = f.read()
        password = _xorhexs(_VNC_SEED, crypted_string)
    finally:
        f.close()

    # TODO: strip NULs
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


def users(human=True):
    '''
    Get a list of users with their privileges to remote management.

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

    return {user:_privs_list(int(privs)) for user, privs in privs.iteritems()}


def set_user_privs(username, naprivs):
    '''
    Set user remote management privileges.

    username
        Valid system user.

    naprivs
        Remote management privileges. A string representing a fixed privilege or set of privileges.
        At the moment, combinations of privileges are not supported. Use one of the predefined strings to set that
        privilege.

        One of:
        - ``enabled`` enabled but nothing set
        - ``text`` send text msgs
        - ``control_notified`` control and observe, show when observing
        - ``control_hidden`` control and observe don't show when observing
        - ``copy`` copy items
        - ``delete_replace`` delete and replace items
        - ``reports`` generate reports
        - ``launch`` open and quit apps
        - ``settings`` change settings
        - ``restart_shutdown`` restart and shutdown
        - ``all`` all enabled
        - ``disabled`` all disabled

    CLI Example:

    .. code-block:: bash

        salt '*' ard.user_privs admin all
    '''
    if naprivs not in _NAPRIVS:
        log.error('Invalid remote management privileges for user {0}: {1}'.format(username, naprivs))
        return False

    if __salt__['dscl.search']('/Search', '/Users', 'name', username) is None:
        log.warning('Cannot set remote management privileges for user: {0}, user was not found'.format(username))
        return False
    else:
        success = __salt__['dscl.create']('.', '/Users/{0}'.format(username), 'naprivs', _NAPRIVS[naprivs])
        return success


