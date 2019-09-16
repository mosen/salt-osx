# -*- coding: utf-8 -*-
'''
Configure the WiFi Preferred Networks settings on macOS
=======================================================

Support for configuring a WiFi Preferred Networks settings on macOS.

Requires the PyObjC Library, bundled with the macOS installer as of 2029.2.0.

.. note::
    This state is primarily for changing and removing existing networks, if
    you would like to add a network, please consider using a macOS profile.

To move a SSID to the top of the preferred networks list.

.. code-block:: yaml

    move_PiedPiper_to_top:
      wifi.top:
        - name: PiedPiper

To move a SSID to the bottom of the preferred networks list.

.. code-block:: yaml

    move_Hooli-Guest_to_the_bottom:
      wifi.bottom:
        - name: Hooli-Guest

To remove a SSID from the list.

.. code-block:: yaml

    remove_Hooli-Guest_network:
      wifi.remove:
        - name: Hooli-Guest

You can also remove a SSID from the list but only when another SSID is present.

Remove Hooli but only when PiedPiper is already in the list.

.. code-block:: yaml

    remove_Hooli_network_if_PiedPiper:
      wifi.remove:
        - name: Hooli
        - required_ssid: PiedPiper

If you don't want to remove a SSID but you preffer it to not AutoJoin.

.. code-block:: yaml

    disable_autojoin_for_Hooli-Guest:
      wifi.disable_autojoin:
        - name: Hooli-Guest

Or make sure that it is set to AutoJoin

.. code-block:: yaml

    enable_autojoin_for_PiedPiper:
      wifi.enable_autojoin:
        - name: PiedPiper

'''

import salt.utils
import salt.utils.platform
import logging
import sys
import os.path
import collections

log = logging.getLogger(__name__)

try:
    import objc, ctypes.util
    from Foundation import NSOrderedSet
    PYOBJC = True
except ImportError:
    PYOBJC = False

__virtualname__ = 'wifi'


def __virtual__():
    """
    Check if macOS and PyObjC is available
    """
    if not salt.utils.platform.is_darwin():
        return (False, 'module: mac_wifi only available on macOS.')
    if not PYOBJC:
        return (False, 'PyObjC not available.')
    return __virtualname__


def top(name):
    '''
    Will place the provided SSID name to the top of the WiFi preferred network
    list.

    name:
        The name of the SSID to move to the top of the list.

    .. code-block:: yaml

        move_PiedPiper_to_top:
          wifi.top:
            - name: PiedPiper

    '''
    ret = {'name': name,
           'result': True,
           'changes': {},
           'comment': ''}

    # get the current wifi position
    current_position = __salt__['wifi.ssid_index'](name)

    # check the position of current ssid.
    if current_position is 0:
        ret['comment'] = 'SSID [{}] is already at the top'.format(name)
        return ret

    # if not found in the list we can return okay.
    if current_position is None:
        ret['comment'] = 'SSID [{}] was not found in the list.'.format(name)

    # testing... check... check....
    if __opts__['test'] == True:
        ret['comment'] = ('SSID [{}] will be removed'.format(name))
        ret['result'] = None
        return ret

    # need to change to top
    move_to_top = __salt__['wifi.top'](name)

    if not move_to_top:
        ret['result'] = False
        ret['comment'] = 'Failed to move SSID [{}] to the top'.format(name)
        return ret

    new_position = __salt__['wifi.ssid_index'](name)

    if new_position is not 0:
        # we failed
        ret['result'] = False
        ret['comment'] = ('Failed to change the position '
                        'of SSID [{}].'.format(name))
        return ret

    #sweet sweet success
    ret['comment'] = 'Successfully moved SSID [{}] to the top '\
                        'of the Preferred Network\'s order list.'.format(name)
    ret['changes'].update(
        {name: {'old': 'Was [{}] position(s) from the top of '\
                        'the Preferred Network\'s order list.'.format(
                    current_position),
                'new': 'At the top of the '\
                       'Preferred Network\'s order list.'}})
    return ret


def bottom(name):
    '''
    Will move the provided SSID name to the bottom of the WiFi preferred network
    list.

    name:
        The name of the SSID to move to the bottom.

    .. code-block:: yaml

        # To move an SSID to the bottom of the preferred networks list.
        move_Hooli-Guest_to_the_bottom:
          wifi.bottom:
            - name: Hooli-Guest

    .. note::
        This state will return successful if the SSID name is not in the
        preferred networks order list.
    '''
    ret = {'name': name,
           'result': True,
           'changes': {},
           'comment': ''}

    # get the current wifi position
    current_position = __salt__['wifi.ssid_index'](name, reverse=True)

    # check the position of current ssid.
    if current_position is 0:
        ret['comment'] = 'SSID [{}] is already at the bottom'.format(name)
        return ret

    # if not found in the list we can return okay.
    if current_position is None:
        ret['comment'] = 'SSID [{}] was not found in the list.'.format(name)

    # testing 1... 2... 3...
    if __opts__['test'] == True:
        ret['comment'] = ('SSID [{}] will be moved to the bottom'.format(name))
        ret['result'] = None
        return ret

    # need to move to the bottom
    move_to_bottom = __salt__['wifi.bottom'](name)

    if not move_to_bottom:
        ret['result'] = False
        ret['comment'] = 'Failed to move SSID "{}" to the bottom'.format(name)
        return ret

    new_position = __salt__['wifi.ssid_index'](name, reverse=True)

    if new_position is not 0:
        # we failed to change the position.
        ret['result'] = False
        ret['comment'] = 'Failed to change the position'\
                            ' of SSID "{}"'.format(name)
        return ret

    # success
    ret['comment'] = 'Successfully moved SSID [{}] to the bottom '\
                        'of the Preferred Network\'s order list.'.format(name)
    ret['changes'].update(
        {name: {'old': 'Was [{}] position(s) from the bottom of '\
                       'the Preferred Network\'s order list.'.format(
                        current_position),
                'new': 'At the bottom of the '\
                       'Preferred Network\'s order list.'}})
    return ret


def remove(name, required_ssid=None):
    '''
    Make sure an SSID is in the network list is removed.

    name
        The name of the SSID to remove.

    required_ssid
        Name of the SSID that should be present in the network list before
        removing the SSID. This should be set to the name of another SSID.
        If this SSID is not in the list salt will not remove the given SSID.

    .. code-block:: yaml

        # remove a SSID from the list.
        remove_Hooli-Guest_network:
          wifi.remove:
            - name: Hooli-Guest
    '''
    ret = {'name': name,
           'result': True,
           'changes': {},
           'comment': ''}

    # check if our SSID is present
    name_available = __salt__['wifi.exists'](name)

    if required_ssid and not __salt__['wifi.exists'](required_ssid):
        ret['comment'] = ('Could not find required SSID [{}] in order to make '
                          'changes to [{}].'.format(required_ssid, name))
        return ret

    if not name_available:
        ret['comment'] = ('SSID [{}] is already removed.'.format(name))
        return ret

    if __opts__['test'] == True:
        ret['comment'] = ('SSID [{}] will be removed'.format(name))
        ret['result'] = None
        return ret

    # need to remove the SSID
    remove = __salt__['wifi.remove'](name)

    if not remove:
        ret['result'] = False
        ret['comment'] = 'Failed to remove SSID [{}] from list.'.format(name)
        return ret

    # we removed the SSID Successfully
    ret['comment'] = ('Successfully removed SSID [{}] from '
                     'the Preferred Network\'s order list.'.format(name))

    ret['changes'].update({name: {'old': 'Available.',
                                  'new': 'Removed.'}})

    return ret


def disable_autojoin(name, required_ssid=None, ignore_missing=True):
    '''
    Will turn off AutoJoin for the provided SSID.

    name
        The name of the SSID to disable autojoin.

    required_ssid
        Name of the SSID that should be present in the network list before
        changing the SSID. This should be set to the name of another SSID.
        If this SSID is not in the list salt will not change the given SSID.

    ignore_missing : True
        Salt will ignore return a success by default if the SSID is not
        available, set this to `False` to have salt return as failed if the
        given SSID is missing.
    '''
    ret = {'name': name,
           'result': True,
           'changes': {},
           'comment': ''}

    # see if our SSID is present
    name_available = __salt__['wifi.exists'](name)

    if not name_available and ignore_missing:
        ret['comment'] = ('SSID [{}] is not available, '
                          'no changes needed.'.format(name))
        return ret

    if not name_available and not ignore_missing:
        ret['comment'] = ('SSID [{}] is not available and '
                          'ignore_missing is False.'.format(name))
        ret['result'] = False
        return ret

    if required_ssid and not __salt__['wifi.exists'](required_ssid):
        ret['comment'] = ('Could not find required SSID [{}] in order to make '
                          'changes to [{}].'.format(required_ssid, name))
        return ret

    # check the current state of autojoin.
    autojoin_disabled = __salt__['wifi.autojoin_disabled'](name)

    if autojoin_disabled:
        ret['comment'] = ('AutoJoin for SSID [{}] is already '
                          'disabled.'.format(name))
        return ret

    if __opts__['test'] == True:
        ret['comment'] = ('AutoJoin for SSID [{}] will be disabled'.format(name))
        ret['result'] = None
        return ret

    # we need to disable autojoin
    disable_autojoin = __salt__['wifi.disable_autojoin'](name)

    if not disable_autojoin:
        ret['result'] = False
        ret['comment'] = ('Failed to disable AutoJoin on the'
                          ' SSID [{}]'.format(name))
        return ret

    # all good
    ret['comment'] = 'Successfully disabled autojoin for SSID [{}]'.format(name)
    ret['changes'].update({name: {'old': 'AutoJoin Enabled.',
                                  'new': 'AutoJoin Disabled.'}})
    return ret


def enable_autojoin(name, required_ssid=None, ignore_missing=True):
    '''
    Will turn on AutoJoin for the provided SSID.

    name
        The name of the SSID to enable autojoin.

    required_ssid
        Name of the SSID that should be present in the network list before
        changing the SSID. This should be set to the name of another SSID.
        If this SSID is not in the list salt will not change the given SSID.

    ignore_missing : True
        Salt will return as successful by default if the SSID is not
        available, set this to `False` to have salt return as failed if the
        given SSID is missing.
    '''
    ret = {'name': name,
           'result': True,
           'changes': {},
           'comment': ''}

    # see if our SSID is present
    name_available = __salt__['wifi.exists'](name)

    if not name_available and ignore_missing:
        ret['comment'] = ('SSID [{}] is not available, '
                          'no changes needed.'.format(name))
        return ret

    if not name_available and not ignore_missing:
        ret['comment'] = ('SSID [{}] is not available and '
                          'ignore_missing is False.'.format(name))
        ret['result'] = False
        return ret

    if required_ssid and not __salt__['wifi.exists'](required_ssid):
        ret['comment'] = ('Could not find required SSID [{}] in order to make '
                          'changes to [{}].'.format(required_ssid, name))
        return ret

    # check the current state of autojoin.
    autojoin_enabled = __salt__['wifi.autojoin_enabled'](name)

    if autojoin_enabled:
        ret['comment'] = ('AutoJoin for SSID [{}] is already '
                          'enabled'.format(name))
        return ret

    if __opts__['test'] == True:
        ret['comment'] = ('AutoJoin for SSID [{}] will be enabled'.format(name))
        ret['result'] = None
        return ret

    # we need to disable autojoin
    enable_autojoin = __salt__['wifi.enable_autojoin'](name)

    if not enable_autojoin:
        # we failed to enable autojoin
        ret['result'] = False
        ret['comment'] = ('Failed to enable AutoJoin on the'
                          ' SSID [{}]'.format(name))
        return ret

    # all good
    ret['comment'] = 'Successfully enabled autojoin for SSID [{}]'.format(name)
    ret['changes'].update({name: {'old': 'AutoJoin Disabled.',
                                  'new': 'AutoJoin Enabled.'}})
    return ret