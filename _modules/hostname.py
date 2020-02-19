"""macOS hostname execution module

This is a macOS hostname execution module. It uses /usr/sbin/scutil to
set ComputerName, HostName, and LocalHostName.

HostName corresponds to what most platforms consider to be hostname; it
controls the name used on the commandline and SSH.

However, macOS also has LocalHostName and ComputerName settings.
LocalHostName controls the Bonjour/ZeroConf name, used by services like
AirDrop. ComputerName is the name used for user-facing GUI services, like
the System Preferences/Sharing pane and when users connect to the Mac
over the network.

:maintainer:    Shea Craig <shea.craig@sas.com>
:maturity:      new
:depends:       None
:platform:      darwin
"""


import logging
import re
import subprocess

import salt.utils.mac_utils
from salt.exceptions import CommandExecutionError

log = logging.getLogger(__name__)

__virtualname__ = 'hostname'

NAMES = ('HostName', 'LocalHostName', 'ComputerName')


def __virtual__():
    """Only load if the platform is macOS"""
    if __grains__.get('kernel') != 'Darwin':
        return False
    return __virtualname__


def get(hostname=True, localhostname=True, computername=True):
    """Return hostnames.

    :param name: Name to get.
    :param hostname: Whether to get the HostName. Defaults to True.
    :param localhostname: Whether to get the LocalHostName. Defaults to
        True.
    :param computername: Whether to get the ComputerName. Defaults to
        True.

    :return: Dictionary of name types and their current values.

    CLI Example::

        salt '*' hostname.get taco
    """
    kwargs = locals()
    return {key: _scutil(key) for key in NAMES if kwargs[key.lower()]}


def set(name, hostname=True, localhostname=True, computername=True, safe=True):
    """Set hostnames.

    :param name: Name to set.
    :param hostname: Whether to set the HostName. Defaults to True.
    :param localhostname: Whether to set the LocalHostName. Defaults to
        True.
    :param computername: Whether to set the ComputerName. Defaults to
        True.
    :param safe: Whether to replace disallowed characters with a hyphen.
        Defaults to True.

    :return: Bool indicating success or failure.

    CLI Example::

        salt '*' hostname.set taco
    """
    # Make sure the desired name will work before continuing.
    fqdn = __grains__['fqdn']
    # A bug in python raises an exception for URL strings longer than
    # 63 characters. First, test whether the desired name plus the
    # domain would exceed that.

    # An issue in the python socket code sometimes produces fqdn
    # with no domain. Test both cases.
    if '.' in fqdn and len(fqdn[fqdn.index('.'):]) + len(name) > 63:
        raise CommandExecutionError('Name is too long!')
    elif '.' not in fqdn and len(__grains__['domain']) + len(name) > 63:
        raise CommandExecutionError('Name is too long!')
    # If localhostname is to be set, ensure the characters conform to
    # RFC 1034 section 3.5, lest the shell-out to scutil will fail.

    elif localhostname and not re.match(r'^[0-9A-Z-]+$', name, re.IGNORECASE) and not safe:
        raise CommandExecutionError('Invalid characters for localhostname!')
    # That being said, macOS seems to only loosely follow this, as it
    # will allow names that start with digits. Warn about that, as it's
    # not going to cause this module to fail, but what are you doing?
    elif localhostname and not re.match(r'^[A-Z][0-9A-Z-]*[0-9A-Z]?$', name, re.IGNORECASE):
        logging.warning('Name violates RFC 1034 section 3.5, but will be settable.')

    if safe:
        name = sanitize(name)

    kwargs = locals()
    for key in NAMES:
        if kwargs[key.lower()]:
            _scutil(key, name)
    return all(
        check(name, hostname, localhostname, computername).values())


def check(name, hostname=True, localhostname=True, computername=True):
    """Check to see if hostnames are set correctly.

    :param name: Name to check.
    :param hostname: Whether to check the HostName. Defaults to True.
    :param localhostname: Whether to check the LocalHostName. Defaults to
        True.
    :param computername: Whether to check the ComputerName. Defaults to
        True.

    :return: Dictionary of name types and whether they're set.

    CLI Example::

        salt '*' hostname.check taco
    """
    current = get(hostname, localhostname, computername)
    kwargs = locals()
    return {k: current[k] == name for k in NAMES if kwargs[k.lower()]}


def sanitize(name):
    """Clean a proposed hostname so it it is LocalHostName compliant.

    :param name: Name to sanitize.

    :return: Sanitized name.

    CLI Example::

        salt '*' hostname.sanitize 2L33T_4_u_
    """
    new_name = re.sub(r'[^0-9A-Z-]', '-', name, flags=re.IGNORECASE)
    if new_name != name:
        logging.warning("Hostname was sanitized from '%s' to '%s'.", name, new_name)
    return new_name


def _scutil(key, name=None):
    if name:
        cmd = 'scutil --set {} {}'.format(key, name)
        salt.utils.mac_utils.execute_return_success(cmd)
    else:
        cmd = 'scutil --get {}'.format(key)
        try:
            result = salt.utils.mac_utils.execute_return_result(cmd)
        except CommandExecutionError as error:
            logging.error("The exact message is %s", error.message)
            if key == 'HostName' and 'HostName: not set' in error.message:
                return ''
            else:
                raise error

        return result
