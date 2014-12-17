# -*- coding: utf-8 -*-
'''
manage energy saver/power management settings.

 .. code-block:: yaml

    ac:
      power:
        - settings
        - sleep: 60
        - displaysleep: 10
'''
import salt.utils
import salt.exceptions

POWER_SOURCES = ['ac', 'battery']  # ups
VALID_SETTINGS = ['displaysleep', 'disksleep', 'sleep', 'womp', 'ring', 'autorestart', 'lidwake', 'acwake',
                  'lessbright', 'halfdim', 'sms', 'ttyskeepawake', 'destroyfvkeyonstandby', 'autopoweroff',
                  'autopoweroffdelay']

__virtualname__ = 'power'


def __virtual__():
    """Only load on OSX"""
    return 'plist' if salt.utils.is_darwin() else False


# def mod_init(low):
#     '''
#     Gather all system power settings
#     '''
#     if low['fun'] == 'settings':
#
#         return True
#     else:
#         return False


def settings(name, **kwargs):
    '''
    Enforce power management settings
    '''
    ret = {'name': name, 'changes': {}, 'result': False, 'comment': ''}
    changes = {'old': {}, 'new': {}}

    if name not in POWER_SOURCES:
        raise salt.exceptions.SaltInvocationError(
            'Invalid power source given: {}'.format(name)
        )

    settings = __salt__['pmset.list_settings']()

    pending = {k: v for k, v in kwargs.iteritems() if k in VALID_SETTINGS and settings[name][k] != v}
    changes = {'old': settings[name], 'new': pending}

    if __opts__['test']:
        if changes['new']:
            ret['changes'] = changes
            ret['result'] = None
            ret['comment'] = 'Power settings would have been changed'
        else:
            ret['result'] = None
            ret['comment'] = 'No changes required'
    else:
        if changes['new']:
            success = __salt__['pmset.set_settings'](name, pending)
        else:
            ret['result'] = None
            ret['comment'] = 'No changes required'

    return ret