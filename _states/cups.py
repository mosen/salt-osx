# -*- coding: utf-8 -*-
'''
ensure printers are present or absent, using the CUPS system.

 .. code-block:: yaml

    Printer_Name:
      printer:
        - present
        - description: 'Printer Description'
        - uri: 'lpd://10.0.0.1/queue'
        - location: 'Downstairs'
        - model: 'drv:///sample.drv/generic.ppd'
        - options:
            - PageSize: A4

    Remove_Printer_Name:
      printer:
        - absent

TODO: No support for enable/disable
'''
import logging
import salt.utils

log = logging.getLogger(__name__)

__virtualname__ = 'printer'

def __virtual__():
    '''
    Only work on POSIX-like systems
    '''
    # Disable on Windows, a specific file module exists:
    if salt.utils.is_windows():
        return False

    return __virtualname__

def present(name, description, uri, **kwargs):
    '''
    Add or ensure printer with name given is configured according to state.

    name
        The name of the destination.
        from lpstat(1) - CUPS allows printer names to contain any printable character except SPACE, TAB, "/", and "#"

    description
        The description, often presented to the end user.

    uri
        The URI of the device, which must be one of the schemes listed in `lpinfo -v`

    model
        PPD or script which will be used from the model directory. This is the normal location for drivers
        which are installed with CUPS. Alternatively you can supply a script or PPD outside of the model directory.
        This does not include the model description as printed in `lpinfo -m`, just the relative path.

    interface
        Interface script to use if model is not set.

    ppd
        PPD file to use if model is not set.

    location
        Optional physical location of the printer

    options
        PPD options
    '''
    ret = {'name': name, 'changes': {}, 'result': False, 'comment': ''}
    changes = {'old': {}, 'new': {}}
    create = False
    printerkwargs = {}
    ignored_updates = ['model', 'interface', 'ppd']  # These keys cant be determined after create time.

    for kwarg in kwargs.keys():
        if kwarg == 'model':
            printerkwargs['model'] = kwargs[kwarg]
            if 'interface' in kwargs:
                ret['result'] = False
                ret['comment'] = 'You cannot use both a model and interface argument. They are exclusive.'
                return ret
            if 'ppd' in kwargs:
                ret['result'] = False
                ret['comment'] = 'You cannot use both a model and a ppd argument. They are exclusive.'
                return ret
        elif kwarg == 'interface':
            if 'ppd' in kwargs:
                ret['result'] = False
                ret['comment'] = 'You cannot use both an interface and ppd argument. They are exclusive.'
                return ret
            printerkwargs['interface'] = kwargs[kwarg]
        elif kwarg in ('__id__', 'fun', 'state', '__env__', '__sls__',
                       'order', 'watch', 'watch_in', 'require', 'require_in',
                       'prereq', 'prereq_in'):
            pass
        else:
            printerkwargs[kwarg] = kwargs[kwarg]

    printerkwargs['description'] = description
    printerkwargs['uri'] = uri

    printers = __salt__['cups.printers']()

    if printers is None or name not in printers:
        '''Just add'''
        changes['new'][name] = printerkwargs
        create = True
    else:
        '''Modify only changed attributes'''
        current_printer = printers[name]
        current_ppd_options = __salt__['cups.options'](name)

        changes['new'][name] = {}

        for k, v in printerkwargs.iteritems():
            if k == 'options':
                continue  # Options will be processed separately
            if k in ignored_updates:
                continue
            if k not in current_printer:
                changes['new'][name][k] = v
            elif current_printer[k] != v:
                changes['new'][name][k] = v

        # TODO: Clean this up so you dont need n^2 iterations
        if 'options' in printerkwargs:
            for kopt, vopt in printerkwargs['options'].iteritems():
                for currentopt in current_ppd_options:
                    if currentopt['name'] == kopt and currentopt['selected'] != vopt:
                        log.debug('PPD Option {0} changed, OLD:{1}, NEW:{2}'.format(kopt, currentopt['selected'], vopt))
                        if 'options' not in changes['new']:
                            changes['new'][name]['options'] = dict()
                        changes['new'][name]['options'][kopt] = vopt



    if __opts__['test']:
        if len(changes['new'][name].keys()) == 0:
            ret['result'] = None
            ret['comment'] = 'No changes required'
        else:
            ret['changes'] = changes
            ret['result'] = None

            if create:
                ret['comment'] = 'Printer would have been created.'
            else:
                ret['comment'] = 'Printer would have been modified.'
    else:
        if len(changes['new'][name].keys()) == 0:
            ret['result'] = None
            ret['comment'] = 'No changes required'
        else:
            # Remove these after comparison has been made with cups.printers, there should be a cleaner way to do this.
            changes['new'][name].pop('uri', None)
            changes['new'][name].pop('description', None)

            success = __salt__['cups.add'](name, description, uri, **changes['new'][name])
            if success:
                ret['result'] = True
                ret['comment'] = 'Printer successfully {}.'.format('created' if create else 'modified')
                ret['changes'] = changes
            else:
                ret['result'] = False
                ret['comment'] = 'Failed to {} printer.'.format('create' if create else 'modify')

    return ret


def absent(name):
    '''
    Remove a printer.

    name
        The name of the printer destination to remove.
    '''
    ret = {'name': name, 'changes': {}, 'result': False, 'comment': ''}
    changes = {'old': {}, 'new': {}}

    printers = __salt__['cups.printers']()

    if printers is None or name not in printers:
        ret['result'] = None
        ret['comment'] = 'No changes required'
        return ret

    changes['old'] = printers[name]

    if __opts__['test']:
        ret['result'] = None
        ret['comment'] = 'Printer {} would have been removed.'.format(name)
    else:
        success = __salt__['cups.remove'](name)
        if success:
            ret['result'] = True
            ret['comment'] = 'Printer successfully removed.'
        else:
            ret['comment'] = 'Failed to remove printer.'

    return ret