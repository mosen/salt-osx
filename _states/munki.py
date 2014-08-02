"""
Configure munki tools client preferences.

:maintainer:    Mosen <mosen@github.com>
:maturity:      new
:platform:      darwin
"""

def client(name, identifier):
    '''
    Manage munki tools client preferences

    name
        The state name.

    identifier:
        The client identifier, used to determine the manifest selected by the client.
    '''
    ret = {'name':name, 'changes':{}, 'result':False, 'comment':''}
    changes = {'old':{},'new':{}}

    current_identifier = __salt__['munki.clientid']()

    if current_identifier != identifier:
        ret['comment'] = 'Client Identifier will be changed to "{0}"'.format(identifier)
        changes['old']['identifier'] = current_identifier
        changes['new']['identifier'] = identifier
        ret['result'] = True

    if __opts__['test'] == True:
        ret['result'] = None
        return ret
    else:
        __salt__['munki.set_clientid'](identifier)
        return ret
