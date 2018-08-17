"""
Enable/Disable automatic system updates and control the CatalogURL

:maintainer:    Mosen <mosen@github.com>
:maturity:      new
:platform:      darwin
"""
import salt.utils

__virtualname__ = 'swupd'


def __virtual__():
    """Only load on OSX"""
    return __virtualname__ if salt.utils.platform.is_darwin() else False


def enabled(name):
    '''
    Enforce system software automatic update checking (Not Incl XProtect or App Store)
    '''
    ret = {'name': name, 'changes': {}, 'result': False, 'comment': ''}

    swupd_enabled = __salt__['swupd.scheduled']()

    if not swupd_enabled:
        ret['changes']['old'] = {'enabled': False}
        ret['changes']['new'] = {'enabled': True}
        ret['comment'] = 'Automatic software update checks have been enabled'
    else:
        ret['result'] = True
        ret['comment'] = 'Automatic software update checks already enabled'
        return ret

    if __opts__['test'] == True:
        ret['comment'] = 'Automatic software update checks will be enabled'
        ret['result'] = None
        return ret

    status = __salt__['swupd.schedule'](True)
    ret['result'] = True

    return ret


def disabled(name):
    '''
    Disable system software automatic update checking (Not Incl XProtect or App Store)
    '''
    ret = {'name': name, 'changes': {}, 'result': False, 'comment': ''}

    swupd_enabled = __salt__['swupd.scheduled']()

    if swupd_enabled:
        ret['changes']['old'] = {'enabled': True}
        ret['changes']['new'] = {'enabled': False}
        ret['comment'] = 'Automatic software update checks have been disabled'
    else:
        ret['result'] = True
        ret['comment'] = 'Automatic software update checks are already disabled'
        return ret

    if __opts__['test'] == True:
        ret['comment'] = 'Automatic software update checks will be disabled'
        ret['result'] = None
        return ret

    status = __salt__['swupd.schedule'](False)
    ret['result'] = True

    return ret
