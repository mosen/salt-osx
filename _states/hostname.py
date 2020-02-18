"""State for managing Mac hostnames"""


import logging

import salt.utils.mac_utils
import salt.utils.platform
from salt.exceptions import CommandExecutionError


log = logging.getLogger(__name__)


__virtualname__ = 'hostname'


def __virtual__():
    """Only make available for the Mac platform."""
    if salt.utils.platform.is_darwin():
        return __virtualname__
    else:
        return False, 'state.hostname only available on macOS'


def managed(name, hostname=True, localhostname=True, computername=True, safe=True):
    """Ensure that current hostname is set to name.

    :param name: Name to manage.
    :param hostname: Whether to manage the HostName. Defaults to True.
    :param localhostname: Whether to manage the LocalHostName. Defaults to
        True.
    :param computername: Whether to manage the ComputerName. Defaults to
        True.
    :param safe: Whether to replace disallowed characters with a hyphen.
        Defaults to True.
    """
    ret = {'name': name,
           'changes': {},
           'result': False,
           'comment': ''}

    if safe:
        name = __salt__['hostname.sanitize'](name)

    if len(name) > 15:
        logging.warning('This hostname will be truncated to %s for SMB!', name[:16])

    result = __salt__['hostname.check'](name, hostname, localhostname, computername)

    if all(result.values()):
        ret['result'] = True
        ret['comment'] = 'Hostname is already set to {}.'.format(name)
        return ret

    ret['changes'] = {k: name for k, v in result.items() if not v}

    if __opts__['test']:
        ret['result'] = None
        ret['comment'] = 'Hostname {} would be set.'.format(name)
        return ret

    __salt__['hostname.set'](name, hostname, localhostname, computername)
    result = __salt__['hostname.check'](name, hostname, localhostname, computername)
    ret['result'] = all(result.values())

    if not ret['result']:
        ret['comment'] = 'Name was not set to {}'.format(name)
    else:
        ret['comment'] = 'Name was set to {}'.format(name)

    return ret