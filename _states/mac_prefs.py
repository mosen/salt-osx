# -*- coding: utf-8 -*-
'''
State will write or delete macOS preferences.

Below is a general guide to where the preferences will be written if you
specify a user and host. If you don't specify a runas user it will be written to
to roots directory, otherwise the given Users directory.

{'file': ('/var/root/Library/Preferences/ByHost/domain.xxxx.plist'),
    'domain': domain,
    'user': kCFPreferencesCurrentUser,
    'host': kCFPreferencesCurrentHost
},
{'file': '/var/root/Library/Preferences/domain.plist',
    'domain': domain,
    'user': kCFPreferencesCurrentUser,
    'host': kCFPreferencesAnyHost
},
{'file': '/Library/Preferences/domain.plist',
    'domain': domain,
    'user': kCFPreferencesAnyUser,
    'host': kCFPreferencesCurrentHost
},


.. code-block:: yaml
    write_burrito_location_prefence:
      prefs.write:
        - name: BurritoLocation
        - value: The Mission
        - domain: com.rounded.edges.corp

.. code-block:: yaml
    write_burrito_location_prefence:
      prefs.delete:
        - name: BurritoLocation
        - domain: com.rounded.edges.corp
        - user: True
'''

import salt.utils.platform
import logging
import sys

log = logging.getLogger(__name__)


__virtualname__ = 'prefs'


def __virtual__():
    if salt.utils.platform.is_darwin():
        return __virtualname__

    return (False, 'states.prefs only available on macOS')


def write(name, value, domain, user=None, host=None, runas=None):
    '''
    Set a preference value using CFPreferences.

    name
        The preference key to write.

    value
        The value to which the key should be set, type will match the types
        passed via the state.

    domain
        The domain to which the key and value should be set in.
    '''

    ret = {'name': name,
           'result': True,
           'changes': {},
           'comment': ''}
 
    # get our current value.
    old_value = __salt__['prefs.read'](name, domain, user, host, runas)

    # check if we are set correctly
    if old_value == value:
        ret['comment'] = '{0} {1} is already set to {2}'.format(domain,
                                                                name,
                                                                value)
        return ret

    # we are not so we need set it
    set_val = __salt__['prefs.set'](name, value, domain, user, host, runas)

    if not set_val:
        ret['result'] = False
        ret['comment'] = 'Failed to set {0} {1} to {2}'.format(domain,
                                                               name,
                                                               value)
    else:
        ret['comment'] = '{0} {1} is set to {2}'.format(domain, name, value)
        ret['changes'].update({name: {'old': old_value,
                                      'new': value}})
    return ret


def delete(name, domain, user=None, host=None, runas=None):
    '''
    Delete a Preference Key.

    name
        The preference key to delete.

    domain
        The domain the key should be removed from.
    '''

    ret = {'name': name,
           'result': True,
           'changes': {},
           'comment': ''}

    # get our current value.
    old_value = __salt__['prefs.read'](name, domain, user, host, runas)

    # check if we are set correctly
    if old_value is None:
        ret['comment'] = '{0} {1} is already removed.'.format(domain, name)
        return ret

    # we are not so we need set it
    set_val = __salt__['prefs.set'](name, None, domain, user, host, runas)

    if not set_val:
        ret['result'] = False
        ret['comment'] = 'Failed to remove {0} {1}.'.format(domain, name)
    else:
        ret['comment'] = '{0} {1} has been removed.'.format(domain, name)
        ret['changes'].update({name: {'old': old_value,
                                      'new': 'removed'}})
    return ret
