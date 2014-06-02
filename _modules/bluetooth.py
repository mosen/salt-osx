"""
Enable or disable Bluetooth and Bluetooth Discoverability via BluetoothIO Framework (private)

Credit to Frederik Seiffert for original blueutil source.
Credit to github/toy for discoverable state feature.

:maintainer:    Mosen <mosen@github.com>
:maturity:      new
:depends:       objc
:platform:      darwin
"""

import time
import logging

log = logging.getLogger(__name__)

HAS_LIBS = False
try:
    from ctypes import CDLL, c_int, c_void_p

    IOBluetooth = CDLL('/System/Library/Frameworks/IOBluetooth.framework/Versions/Current/IOBluetooth')

    # Declare private functions in IOBluetooth
    IOBluetoothPreferencesAvailable = IOBluetooth.IOBluetoothPreferencesAvailable
    IOBluetoothPreferencesAvailable.restype = c_int

    IOBluetoothPreferenceGetControllerPowerState = IOBluetooth.IOBluetoothPreferenceGetControllerPowerState
    IOBluetoothPreferenceGetControllerPowerState.restype = c_int

    IOBluetoothPreferenceSetControllerPowerState = IOBluetooth.IOBluetoothPreferenceSetControllerPowerState
    IOBluetoothPreferenceSetControllerPowerState.restype = c_void_p

    IOBluetoothPreferenceGetDiscoverableState = IOBluetooth.IOBluetoothPreferenceGetDiscoverableState
    IOBluetoothPreferenceGetDiscoverableState.restype = c_int

    IOBluetoothPreferenceSetDiscoverableState = IOBluetooth.IOBluetoothPreferenceSetDiscoverableState
    IOBluetoothPreferenceSetDiscoverableState.restype = c_void_p

    HAS_LIBS = True
except ImportError:
    log.debug('Execution module not suitable because one or more imports failed.')

__virtualname__ = 'bluetooth'


def __virtual__():
    '''
    Only load if the platform is correct and we can use PyObjC libs
    '''
    if __grains__.get('kernel') != 'Darwin':
        return False

    if not HAS_LIBS:
        return False

    # System does not support bluetooth
    if not IOBluetoothPreferencesAvailable():
        return False

    return __virtualname__


def _btPowerState():
    '''
    Get the Bluetooth power status

    0|1
    '''
    return IOBluetoothPreferenceGetControllerPowerState()


def _btSetPowerState(powerState):
    '''
    Set the Bluetooth power status
    :param powerState: 0|1
    '''
    IOBluetoothPreferenceSetControllerPowerState(powerState)
    time.sleep(
        2)  # There is some delay between changing the power and the getter returning the right information. toy@github estimates 10 seconds.
    if (_btPowerState() != powerState):  # Cannot set power state
        return False
    else:
        return True


def _btDiscoverState():
    '''
    Is this device discoverable?

    Returns 0 or 1
    '''
    return IOBluetoothPreferenceGetDiscoverableState()


def _btSetDiscoverState(discoverState):
    '''
    Set Bluetooth discoverability

    0 or 1
    '''
    IOBluetoothPreferenceSetDiscoverableState(discoverState)
    time.sleep(2)
    if (_btDiscoverState() != discoverState):
        return False
    else:
        return True


def on():
    '''
    Set Bluetooth power on

    CLI Example:

    .. code-block:: bash

        salt '*' bluetooth.on
    '''
    return _btSetPowerState(1)


def off():
    '''
    Set Bluetooth power off

    CLI Example:

    .. code-block:: bash

        salt '*' bluetooth.off
    '''
    return _btSetPowerState(0)


def available():
    '''
    Check if bluetooth preferences are available.
    This may indicate the presence of Bluetooth support.

    CLI Example:

    .. code-block:: bash

        salt '*' bluetooth.available
    '''
    return True if IOBluetoothPreferencesAvailable() else False


def status():
    '''
    Get Bluetooth power status

    CLI Example:

    .. code-block:: bash

        salt '*' bluetooth.off
    '''
    return 'on' if _btPowerState() else 'off'


def discover():
    '''
    Enable Bluetooth discovery of this node

    CLI Example:

    .. code-block:: bash

        salt '*' bluetooth.discover
    '''
    return _btSetDiscoverState(1)


def nodiscover():
    '''
    Disable Bluetooth discovery of this node

    CLI Example:

    .. code-block:: bash

        salt '*' bluetooth.nodiscover
    '''
    return _btSetDiscoverState(0)


def discoverable():
    '''
    Is this node discoverable

    CLI Example:

    .. code-block:: bash

        salt '*' bluetooth.discoverable
    '''
    if _btDiscoverState():
        return True
    else:
        return False
