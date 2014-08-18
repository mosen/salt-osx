"""
Enable or disable Bluetooth power and discoverability.

:maintainer:    Mosen <mosen@github.com>
:maturity:      new
:platform:      darwin
"""
import salt.utils

def __virtual__():
    """Only load on OSX"""
    return 'bluetooth' if salt.utils.is_darwin() else False


def managed(name, enabled, discoverable=True):
    '''
    Enforce Bluetooth power/discoverability state.

    name
        The state name, in this case Bluetooth is global and therefore name can be anything.
        I suggest 'system'.

    enabled
        If True, Bluetooth will be enabled, otherwise it will be disabled.

    discoverable : True
        If power is on, you can optionally select whether this device is discoverable by others. If power is set to
        off, then this parameter has no effect.

    '''
    ret = {'name':name, 'changes':{}, 'result':False, 'comment':''}

    current_power = __salt__['bluetooth.status']()
    current_discoverability = __salt__['bluetooth.discoverable']()
    changes = { 'old':{}, 'new':{} }


    if current_power == 'off' and enabled == False:
        ret['result'] = True
        ret['comment'] = 'Bluetooth is already disabled'

    if current_power == 'off' and enabled == True:
        ret['comment'] = 'Bluetooth will be enabled'

        changes['old']['enabled'] = False
        changes['new']['enabled'] = True

        current_power = 'on'


    if current_power == 'on' and enabled == False:
        ret['comment'] = 'Bluetooth will be disabled'

        changes['old']['enabled'] = True
        changes['new']['enabled'] = False

        current_power = 'off'

    changed_text = 'discoverable' if discoverable else 'undiscoverable'

    # Discoverability doesnt matter if power is off
    if current_power == 'on':
        if current_discoverability == discoverable:
            ret['comment'] = 'Bluetooth device is already %s' % changed_text

        if current_discoverability != discoverable:
            ret['comment'] = 'Bluetooth discoverability will be changed to %s' % changed_text

            changes['old']['discoverable'] = current_discoverability
            changes['new']['discoverable'] = discoverable


    # Now make required changes, or log them if in test mode
    if __opts__['test'] == True:
        ret['result'] = None
        ret['changes'] = changes
        return ret
    else:
        if 'enabled' in changes['new']:
            power_method = {True:'bluetooth.on', False:'bluetooth.off'}[changes['new']['enabled']]
            changed_power = __salt__[power_method]()

            if 'discoverable' in changes['new']:
                discover_method = {True:'bluetooth.discover', False:'bluetooth.nodiscover'}[changes['new']['discoverable']]
                changed_discoverability = __salt__[discover_method]()

            # TODO: Check if either method actually failed. Current return status (of bluetooth.on etc) has nothing to do with failure.

            ret['result'] = True
            ret['changes'] = changes
            return ret
        else:
            # Nothing to change
            ret['result'] = None
            return ret

