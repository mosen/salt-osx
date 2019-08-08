# -*- coding: utf-8 -*-
'''
Management of preference list values
====================================

Management of specific keys and their values can be done using these states.

.. code-block:: yaml

    /Library/Preferences/x.plist:
        plist.managed_keys:
            - key:
                nested_key: 'value'
            - key_two: True

.. note::

    This uses native API by default, and therefore should be safe with files managed by cfprefsd.
    Apple still does not recommend modification of property lists if the owning process is running.

'''
import salt.utils


__virtualname__ = 'plist'


def __virtual__():
    '''Only load on macOS'''
    if salt.utils.platform.is_darwin():
        return __virtualname__

    return (False, 'mac_plist is only available on macOS.')


def managed_keys(name, **keys):
    '''
    This function manages a specific list of keys within a named property list file.

    name
        The full path of the property list file to manage.

    keys
        Every other property of this state is used to describe a key hierarchy and a value to manage.

        When describing key values in YAML, you are restricted to types easily translated.

    '''
    ret = {'name':name, 'result':False, 'changes':{}, 'comment':''}
    changes = {'old': __salt__['plist.read_keys'](name, keys), 'new': {}}

    changed = __salt__['plist.write_keys'](name, keys, __opts__['test'])

    if changed:
        changes['new'] = changed
        ret['changes'] = changes

    if __opts__['test'] == True:
        ret['comment'] = 'Values will be changed' if changed else 'File is in the correct state'
        ret['result'] = None if changed else True
    else:
        ret['comment'] = 'Values changed' if changed else 'File is in the correct state'
        ret['result'] = True

    return ret


def absent_keys(name, **keys):
    '''
    This function will remove a list of keys, given a structure that mimics their location in the property list.

    name
        The full path of the property list file to manage
    keys
        All other properties are a description of key locations to remove, with the deepest keys, or leaf nodes
        being removed.
    '''
    ret = {'name':name, 'result':False, 'changes':{}, 'comment':''}
    changes = {'old': __salt__['plist.read_keys'](name, keys), 'new': {}}

    changed = __salt__['plist.delete_keys'](name, keys, __opts__['test'])

    if changed:
        changes['new'] = changed
        ret['changes'] = changes

    if __opts__['test'] == True:
        ret['comment'] = 'Keys will be removed' if changed else 'File is in the correct state'
        ret['result'] = None if changed else True
    else:
        ret['comment'] = 'Keys removed' if changed else 'File is in the correct state'
        ret['result'] = True

    return ret


def managed(name, **keys):
    '''
    Manage an entire plist file on MacOS.

    name
        The Path to the plist file.

    keys
        Key value pairs for the content of the plist dictionary.
    '''

    ret = {'name': name,
           'result': True,
           'changes': {},
           'comment': ''}

    # get our current value.
    current_keys = __salt__['plist.read'](name)

    # check if we are set correctly
    if current_keys == keys:
        ret['comment'] = 'plist at {} is already set correctly.'.format(name)
        return ret

    # we are not so we need set it
    set_val = __salt__['plist.write'](name, keys)

    if not set_val:
        ret['result'] = False
        ret['comment'] = 'Failed to set {0} to {1}'.format(name, keys)
    else:
        ret['comment'] = 'Successfully set plist file {}'.format(name)
        ret['changes'].update({name: {'old_plist': current_keys,
                                      'new_plist': keys}})
    return ret
