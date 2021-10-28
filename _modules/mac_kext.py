from __future__ import absolute_import, unicode_literals, print_function

# Import python libs
import logging
import os

# Import salt libs
import salt.utils.platform
from salt.exceptions import CommandExecutionError
from salt.utils.versions import LooseVersion as _LooseVersion

# Define the module's virtual name
__virtualname__ = 'kext'

def __virtual__():
    '''
    Only for macOS with launchctl
    '''
    if not salt.utils.platform.is_darwin():
        return (False, 'Failed to load the mac_kext module:\n'
                       'Only available on macOS systems.')

    if not os.path.exists('/sbin/kextunload'):
        return (False, 'Failed to load the mac_kext module:\n'
                       'Required binary not found: "/sbin/kextunload"')

    if not os.path.exists('/usr/sbin/kextstat'):
        return (False, 'Failed to load the mac_kext module:\n'
                       'Required binary not found: "/usr/sbin/kextstat"')

    return __virtualname__


log = logging.getLogger(__name__)


def unload(name):
    '''
    Unload a kext at the given path.

    name Path to Kext to unload.

    '''
    cmd = '/sbin/kextunload {}'.format(name)
    ret = __salt__['cmd.run_all'](cmd)
    # Raise an error or return successful result
    if ret['retcode']:
        out = 'Failed to {0} service:\n'.format(cmd)
        out += 'stdout: {0}\n'.format(ret['stdout'])
        out += 'stderr: {0}\n'.format(ret['stderr'])
        out += 'retcode: {0}'.format(ret['retcode'])
        raise CommandExecutionError(out)

    return True


def load(name):
    '''
    load a kext at the given path.

    name Path to Kext to unload.

    '''
    cmd = '/sbin/kextload {}'.format(name)
    ret = __salt__['cmd.run_all'](cmd)
    # Raise an error or return successful result
    if ret['retcode']:
        out = 'Failed to {0} service:\n'.format(cmd)
        out += 'stdout: {0}\n'.format(ret['stdout'])
        out += 'stderr: {0}\n'.format(ret['stderr'])
        out += 'retcode: {0}'.format(ret['retcode'])
        raise CommandExecutionError(out)

    return True


def running(name):
    '''
    The name of the kext to check to see if it's loaded, this can be checked
    by running ``kextstat -list-only`` and looking for your kext name.

    name:
        the bundle_id of the kext

    #TODO this is doing a very loose check on the name so this will return True
    if you check for kext foo.bar.ponies and kext foo.bar.ponies.wanna.fly
    is running. We should do a more strict check. But Kexts are dying soon so
    oh well.

    #TODO get the CFBundleIdentifier from the kext at a path, so we specify a
    path here if we want. not just the bundle ID.
    '''
    cmd = '/usr/sbin/kextstat  -list-only -bundle-id {}'.format(name)
    ret = __salt__['cmd.run_all'](cmd)
    # Raise an error or return successful result
    if ret['retcode']:
        out = 'Failed to {0} service:\n'.format(cmd)
        out += 'stdout: {0}\n'.format(ret['stdout'])
        out += 'stderr: {0}\n'.format(ret['stderr'])
        out += 'retcode: {0}'.format(ret['retcode'])
        raise CommandExecutionError(out)

    stdout =  ret['stdout']
    if not stdout:
        return False

    # split the output into a list so we can check each line for the name
    stdout_list = stdout.split('\n')
    log.trace('Running kext list: {}'.format(stdout_list))

    # go through each line to see if the name we want is running.
    for kext in stdout_list:
        if name in kext:
            return True

    # if we got here out kext isn't running
    return False
