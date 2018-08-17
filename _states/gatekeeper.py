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

    if not spctl_enabled:
        ret['changes']['old'] = {'enabled': False}
        ret['changes']['new'] = {'enabled': True}
        ret['comment'] = 'Gatekeeper has been enabled'
    else:
        ret['result'] = True
        ret['comment'] = 'Gatekeeper is already enabled'
        return ret

    if __opts__['test'] == True:
        ret['comment'] = 'Gatekeeper will be enabled'
        ret['result'] = None
        return ret

    status = __salt__['spctl.enable']()
    ret['result'] = True

    return ret


def disabled(name):
    '''
    Enforce gatekeeper as being disabled
    '''
    ret = {'name': name, 'changes': {}, 'result': False, 'comment': ''}

    spctl_enabled = __salt__['spctl.enabled']()

    if spctl_enabled:
        ret['changes']['old'] = {'enabled': True}
        ret['changes']['new'] = {'enabled': False}
        ret['comment'] = 'Gatekeeper has been disabled'
    else:
        ret['result'] = True
        ret['comment'] = 'Gatekeeper is already disabled'
        return ret

    if __opts__['test'] == True:
        ret['comment'] = 'Gatekeeper will be disabled'
        ret['result'] = None
        return ret

    status = __salt__['spctl.disable']()
    ret['result'] = True

    return ret
