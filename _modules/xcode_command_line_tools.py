"""macOS Xcode command line tools module

This is a macOS execution module which will install and report on the
status of the Xcode command line tools package, which among other
things contains git, gcc, etc.

:maintainer:    Shea Craig <shea.craig@sas.com>
:maturity:      new
:depends:       None
:platform:      darwin
"""


import logging
import os
import re
from distutils.version import StrictVersion

import salt.utils.mac_utils
from salt.exceptions import CommandExecutionError


log = logging.getLogger(__name__)

__virtualname__ = 'xcode_command_line_tools'


def __virtual__():
    """Only load if the platform is macOS"""
    if __grains__.get('kernel') != 'Darwin':
        return False
    if StrictVersion(__grains__['osrelease']) < StrictVersion('10.9'):
        return False
    return __virtualname__


def install():
    """Install the Xcode command line tools.

    :return: Bool indicating success or failure.

    CLI Example::

        salt '*' xcode_command_line_tools.install
    """
    trigger = "/tmp/.com.apple.dt.CommandLineTools.installondemand.in-progress"

    # Touch the trigger file to coerce softwareupdate into offering the
    # command line tools.
    with open(trigger, 'w') as trigger_handle:
        trigger_handle.write('')

    available_updates = __salt__['softwareupdate.list_available']()
    logging.debug('Available updates: %s', available_updates)
    # Example label 10.14:
    # Command Line Tools (macOS Mojave version 10.14) for Xcode-10.3
    # Example label Beta:
    # Command Line Tools beta 6 for Xcode-11.0
    # Example Catalina result:
    # Command Line Tools for Xcode-11.0

    pattern = re.compile(r'Command Line Tools[\(\)\w\s.]* for Xcode-[\d.]+')

    # Filter out versions that aren't for this OS release.
    candidates = [(update, version) for update, version in available_updates.items()
                  if pattern.match(update)]
    logging.debug('Command Line Tools candidates: %s', candidates)

    if candidates:
        # Sort by version number and get the newest (last) update name.
        newest_update = sorted(candidates, key=lambda i: StrictVersion(i[1]))[-1][0]
        logging.debug('Selected Command Line Tools: %s', newest_update)
        cmd = ['softwareupdate', '--install', newest_update]
        __salt__['cmd.run'](cmd)
        result = check()
    else:
        result = False

    # Remove the trigger file so softwareupdate doesn't continue to
    # offer the command line tools.
    os.unlink(trigger)

    return result


def check():
    """Check to see if the command line tools are installed.

    This includes checking that they are installed for this OS version.

    :return: Boolean.

    CLI Example::

        salt '*' xcode_command_line_tools.check
    """
    cmd = ['xcode-select', '-p']
    try:
        return salt.utils.mac_utils.execute_return_success(cmd)
    except CommandExecutionError:
        return False
