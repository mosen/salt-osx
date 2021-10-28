# -*- coding: utf-8 -*-
'''
Management of Kernel Extensions on macOS
====================================

To ensure that Kernel Extensions are running (loaded) or dead (unloaded/stopped)
can be done with these states

.. code-block:: yaml

    ensure_kext_is_dead:
    kext.dead:
        - name: /path/to/kext/foo.kext
        - bundleid: com.kext.bundleid

    ensure_kext_is_running:
    kext.running:
        - name: /path/to/kext/foo.kext
        - bundleid: com.kext.bundleid
'''

import salt.utils.platform
import logging
import os

log = logging.getLogger(__name__)


__virtualname__ = 'kext'


def __virtual__():
    """
    Only macOS
    """
    if not salt.utils.platform.is_darwin():
        return (False, 'state.mac_kext only available on macOS.')

    return __virtualname__


def running(name, bundleid):
    '''
    Ensure that the given kext is loaded/running

    name:
        The path to the kext to keep loaded

    bundleid:
        The bundle-id of the kext (CFBundleIdentifier)

    '''
    ret = {'name': name,
           'result': True,
           'changes': {},
           'comment': ''}

    if not os.path.exists(name):
        ret['result'] = False
        ret['comment'] = 'Could not find required kext at [{}].'.format(name)
        return ret

    # check to see if our kext is running.
    kext_running = __salt__['kext.running'](bundleid)

    # if our kext is already running then we are how we should be.
    if kext_running:
        return ret

    # if we get here our kext isn't running, Here we should check to see if
    # we are in test mode, if so, re can return accordingly.
    if __opts__['test']:
        ret['result'] = None
        ret['comment'] = 'Kext {0} will be started'.format(name)
        return ret

    # so we know we aren't in test mode, and our kext isn't running properly
    # we can call our execution module to load the kext
    start_kext = __salt__['kext.load'](name)

    # if our attempt to load the kext returned false then we didn't
    # start it successfully, set our return data to failed.
    if not start_kext:
        ret['result'] = False
        ret['comment'] = 'Failed to load kext {}.'.format(name)
        return ret

    # fill out our return information the state data.
    ret['comment'] = 'Successfully loaded kext {}.'.format(name)
    ret['changes'].update({name: {'old': 'Dead',
                                  'new': 'Running'}})
    return ret


def dead(name, bundleid):
    '''
    Ensure that the given kext is not loaded/running

    name:
        The path to the kext to keep unload

    bundleid:
        The bundle-id of the kext (CFBundleIdentifier)

    '''
    ret = {'name': name,
           'result': True,
           'changes': {},
           'comment': ''}

    # check to see if our kext is running.
    kext_running = __salt__['kext.running'](bundleid)

    if not kext_running:
        return ret

    if __opts__['test']:
        ret['result'] = None
        ret['comment'] = 'Kext {0} will be stopped'.format(bundleid)
        return ret

    disable_kext = __salt__['kext.unload'](name)

    if not disable_kext:
        ret['result'] = False
        ret['comment'] = 'Failed to unload kext {}.'.format(name)
        return ret


    ret['comment'] = 'Successfully unloaded kext {}.'.format(name)
    ret['changes'].update(
        {name: {'old': 'Running',
                'new': 'Dead'}})
    return ret