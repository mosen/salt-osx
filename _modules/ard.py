# -*- coding: utf-8 -*-
'''
manage the "remote management" service via kickstart and property lists.
'''
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


def users():
    '''
    Get a list of users with their privileges to remote management.

    CLI Example:

    .. code-block:: bash

        salt '*' ard.users
    '''
    return __salt__['dscl.list']('.', '/Users', 'naprivs')

def set_user_privs(username, naprivs):
    '''
    Set user remote management privileges.

    username
        Valid system user.

    naprivs
        Remote management privileges.

    CLI Example:

    .. code-block:: bash

        salt '*' ard.user_privs admin x
    '''
    if __salt__['dscl.search']('/Search', '/Users', 'name', username) is None:
        raise CommandExecutionError('Cannot set privileges for user: {0}, user was not found'.format(username))
    else:
        pass
