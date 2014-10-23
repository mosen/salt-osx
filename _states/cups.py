"""
Add, modify and remove printers.
"""
import salt.utils

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
    # Note: cannot determine the model, interface script, or ppd from lpstat output. These are excluded.
    compare = ['description', 'uri', 'location', 'options']

    printers = __salt__['cups.printers']()

    if name not in printers:
        added = __salt__['cups.add'](name, description, uri, kwargs)
        if added:
            changes['new'] = added
        else:
            # Error: failed to add
            ret['comment'] = 'Error adding printer'
            return ret
    else:
        # TODO: Unfinished
        raise Exception()



def absent(name):
    '''
    Remove a printer.

    name
        The name of the printer destination to remove.
    '''
    ret = {'name': name, 'changes': {}, 'result': False, 'comment': ''}
    changes = {'old': {}, 'new': {}}