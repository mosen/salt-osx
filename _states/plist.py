# -*- coding: utf-8 -*-
"""
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

"""
import salt.utils


def __virtual__():
    """Only load on OSX"""
    return 'plist' if salt.utils.is_darwin() else False


def managed_keys(name, **keys):
    """
    This function manages a specific list of keys within a named property list file.

    name
        The full path of the property list file to manage.

    keys
        Every other property of this state is used to describe a key hierarchy and a value to manage.

        When describing key values in YAML, you are restricted to types easily translated.

    """
    ret = {'name':name, 'result':False, 'changes':{}, 'comment':''}
    changes = {'old': __salt__['plist.read_keys'](name, keys), 'new': {}}

    changed = __salt__['plist.write_keys'](name, keys, __opts__['test'])

    if changed:
        changes['new'] = changed
        ret['changes'] = changes

    if __opts__['test'] == True:
        ret['comment'] = 'Values will be changed' if changed else 'No changes will be required'
        ret['result'] = None
    else:
        ret['comment'] = 'Values changed' if changed else 'No changes required'
        ret['result'] = True if changed else None

    return ret

def absent_keys(name, **keys):
    """
    This function will remove a list of keys, given a structure that mimics their location in the property list.

    name
        The full path of the property list file to manage
    keys
        All other properties are a description of key locations to remove, with the deepest keys, or leaf nodes
        being removed.
    """
    ret = {'name':name, 'result':False, 'changes':{}, 'comment':''}
    changes = {'old': __salt__['plist.read_keys'](name, keys), 'new': {}}

    changed = __salt__['plist.delete_keys'](name, keys, __opts__['test'])

    if changed:
        changes['new'] = changed
        ret['changes'] = changes

    if __opts__['test'] == True:
        ret['comment'] = 'Keys will be removed' if changed else 'No keys will be removed'
        ret['result'] = None
    else:
        ret['comment'] = 'Keys removed' if changed else 'No keys found for removal'
        ret['result'] = True if changed else None

    return ret