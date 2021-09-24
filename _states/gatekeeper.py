"""
Enable or disable gatekeeper system wide

:maintainer:    Mosen <mosen@github.com>
:maturity:      new
:platform:      darwin
"""
import salt.utils

__virtualname__ = 'gatekeeper'


def __virtual__():
    """Only load on OSX"""
    return __virtualname__ if salt.utils.platform.is_darwin() else False


def enabled(name):
    '''
    Enforce gatekeeper as being enabled.
    '''
    ret = {'name': name, 'changes': {}, 'result': False, 'comment': ''}

    spctl_enabled = __salt__['spctl.enabled']()

    if spctl_enabled:
        ret['result'] = True
        ret['comment'] = 'Gatekeeper is already enabled'
        return ret

    if __opts__['test'] == True:
        ret['comment'] = 'Gatekeeper will be enabled'
        ret['result'] = None
        return ret

    status = __salt__['spctl.enable']()
    if not status:
        ret['comment'] = 'Gatekeeper failed to enable.'
        return ret

    ret['result'] = True
    ret['comment'] = 'Gatekeeper has been enabled'
    ret['changes']["GateKeeper"] = {"old": "disabled", "new": "enabled"}
    return ret


def disabled(name):
    '''
    Enforce gatekeeper as being disabled
    '''
    ret = {'name': name, 'changes': {}, 'result': False, 'comment': ''}

    spctl_enabled = __salt__['spctl.enabled']()

    if not spctl_enabled:
        ret['result'] = True
        ret['comment'] = 'Gatekeeper is already enabled'
        return ret

    if __opts__['test'] == True:
        ret['comment'] = 'Gatekeeper will be disabled'
        ret['result'] = None
        return ret

    status = __salt__['spctl.disable']()
    if not status:
        ret['comment'] = 'Gatekeeper failed to disable.'
        return ret

    ret['result'] = True
    ret['comment'] = 'Gatekeeper has been disabled'
    ret['changes']["GateKeeper"] = {"old": "enabled", "new": "disabled"}
    return ret
