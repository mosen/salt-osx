# -*- coding: utf-8 -*-
'''
manage energy saver/power management settings.

Please see the man page for pmset(1) for further explanation of what each option does.
For convenience, options that were 0/1 are converted to True or False.

 .. code-block:: yaml

    ac:
      power:
        - settings
        - sleep: 60
        - displaysleep: 10
        - disksleep: 120
'''
import logging
import salt.utils
import salt.exceptions

log = logging.getLogger(__name__)

POWER_SOURCES = ['ac', 'battery']  # ups
VALID_SETTINGS = ['displaysleep', 'disksleep', 'sleep', 'womp', 'ring', 'autorestart', 'lidwake', 'acwake',
                  'lessbright', 'halfdim', 'sms', 'ttyskeepawake', 'destroyfvkeyonstandby', 'autopoweroff',
                  'autopoweroffdelay']

__virtualname__ = 'power'


def __virtual__():
    """Only load on OSX"""
    return __virtualname__ if salt.utils.is_darwin() else False


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

    if name not in settings:
        ret['result'] = None
        ret['comment'] = 'Power source not available on this minion: {0}'.format(name)

        return ret

    def _validChange(item):
        '''Determine if given pair is a valid setting, and is an update'''
        k, v = item

        if k not in VALID_SETTINGS:
            return False

        if k not in settings[name]:
            return True

        if settings[name][k] != v:
            return True

        return False

    pending = dict(filter(_validChange, kwargs.iteritems()))

    # pmset will fail if disk sleep is never and system sleep is defined
    if 'disksleep' in pending and 'sleep' in pending:
        if pending['disksleep'] == 0 and pending['sleep'] > 0:
            ret['result'] = False
            ret['comment'] = 'It is not possible to disable disk sleep when system sleep is enabled'
            return ret


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
            success = __salt__['pmset.set_settings'](name, **pending)
            ret['result'] = success

            if success:
                ret['comment'] = 'Power settings applied successfully'
            else:
                ret['comment'] = 'Could not apply power settings'
        else:
            ret['result'] = None
            ret['comment'] = 'No changes required'

    return ret