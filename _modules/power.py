"""
Interact with the power management of the osx minion

:maintainer:    Mosen <mosen@github.com>
:maturity:      new
:depends:       ctypes
:platform:      darwin
"""

# restart/shutdown/logout/sleep
# https://developer.apple.com/library/mac/qa/qa1134/_index.html

import logging

log = logging.getLogger(__name__)

HAS_LIBS = False
try:
    from ctypes import CDLL

    IOKit = CDLL("/System/Library/Frameworks/IOKit.framework/Versions/Current/IOKit")

    IOPMSleepSystem = IOKit.IOPMSleepSystem
    IOPMFindPowerManagement = IOKit.IOPMFindPowerManagement  # restype is io_connect_t which is mach_port_t which is just a Uint32
    IOServiceClose = IOKit.IOServiceClose

    HAS_LIBS = True
except ImportError:
    log.debug('Execution module not suitable because one or more imports failed.')

__virtualname__ = 'power'


def __virtual__():
    '''
    Only load if the platform is correct and we can use PyObjC libs
    '''
    if __grains__.get('kernel') != 'Darwin':
        return False

    if not HAS_LIBS:
        return False

    return __virtualname__


# Apple recommends using IOKit instead of apple events for system daemons. Because the minion is headless and runs like
# a daemon, I am using IOKit here too.
def sleep():
    '''
    Sleep the system IMMEDIATELY

    CLI Example:

    .. code-block:: bash

        salt '*' power.sleep
    '''
    fb = IOPMFindPowerManagement(None)
    IOPMSleepSystem(fb)
    IOServiceClose(fb)  # Mach ports always need to be closed


# Apple also recommends just executing shutdown(8) instead of any system API for daemon processes.
def shutdown(when='now'):
    '''
    Shut the system down, with optional time specifier as per man shutdown(8)

    CLI Example:

    .. code-block:: bash

        salt '*' power.shutdown <now|+minutes|yymmddhhmm>
    :return:
    '''
    return __salt__['cmd.run']("shutdown %s" % when)


def restart(when='now'):
    '''
    Restart the system, with optional time specifier as per man shutdown(8)

    CLI Example:

    .. code-block:: bash

        salt '*' power.restart <now|+minutes|yymmddhhmm>
    :return:
    '''
    return __salt__['cmd.run']("shutdown -r %s" % when)