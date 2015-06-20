"""
Enable or disable Bluetooth and Bluetooth Discoverability via BluetoothIO Framework (private)

Credit to Frederik Seiffert for original blueutil source.
Credit to github/toy for discoverable state feature.

NOTE: In current versions of Mac OS X, discoverability is controlled by whether the Bluetooth System
Preferences pane is open.

:maintainer:    Mosen <mosen@github.com>
:maturity:      new
:depends:       ctypes
:platform:      darwin
"""

import time
import logging

log = logging.getLogger(__name__)

HAS_LIBS = False
try:
    from ctypes import CDLL, c_int, c_void_p

    _IOBluetooth = CDLL('/System/Library/Frameworks/IOBluetooth.framework/Versions/Current/IOBluetooth')

    # Declare private functions in IOBluetooth
    _IOBluetoothPreferencesAvailable = _IOBluetooth.IOBluetoothPreferencesAvailable
    _IOBluetoothPreferenceGetControllerPowerState = _IOBluetooth.IOBluetoothPreferenceGetControllerPowerState

    _IOBluetoothPreferenceSetControllerPowerState = _IOBluetooth.IOBluetoothPreferenceSetControllerPowerState
    _IOBluetoothPreferenceSetControllerPowerState.restype = c_void_p

    _IOBluetoothPreferenceGetDiscoverableState = _IOBluetooth.IOBluetoothPreferenceGetDiscoverableState

    _IOBluetoothPreferenceSetDiscoverableState = _IOBluetooth.IOBluetoothPreferenceSetDiscoverableState
    _IOBluetoothPreferenceSetDiscoverableState.restype = c_void_p

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
    if not _IOBluetoothPreferencesAvailable():
        return False

    return __virtualname__


def _bt_power_state():
    '''
    Get the Bluetooth power status

    0|1
    '''
    return _IOBluetoothPreferenceGetControllerPowerState()


def _bt_set_power_state(state):
    '''
    Set the Bluetooth power status
    :param state: 0|1
    '''
    _IOBluetoothPreferenceSetControllerPowerState(state)
    time.sleep(
        2)  # There is some delay between changing the power and the getter returning the right information.
            # toy@github estimates 10 seconds.
    if _bt_power_state() != state:  # Cannot set power state
        return False
    else:
        return True


def _bt_discover_state():
    '''
    Is this device discoverable?

    Returns 0 or 1
    '''
    return _IOBluetoothPreferenceGetDiscoverableState()


def _bt_set_discover_state(state):
    '''
    Set Bluetooth discoverability

    0 or 1
    '''
    _IOBluetoothPreferenceSetDiscoverableState(state)
    time.sleep(2)
    if _bt_discover_state() != state:
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
    return _bt_set_power_state(1)


def off():
    '''
    Set Bluetooth power off

    CLI Example:

    .. code-block:: bash

        salt '*' bluetooth.off
    '''
    return _bt_set_power_state(0)


def available():
    '''
    Check if bluetooth preferences are available.
    This may indicate the presence of Bluetooth support.

    CLI Example:

    .. code-block:: bash

        salt '*' bluetooth.available
    '''
    return True if _IOBluetoothPreferencesAvailable() else False


def status():
    '''
    Get Bluetooth power status

    CLI Example:

    .. code-block:: bash

        salt '*' bluetooth.status
    '''
    return 'on' if _bt_power_state() else 'off'


def discover():
    '''
    Enable Bluetooth discovery of this node

    CLI Example:

    .. code-block:: bash

        salt '*' bluetooth.discover
    '''
    return _bt_set_discover_state(1)


def nodiscover():
    '''
    Disable Bluetooth discovery of this node

    CLI Example:

    .. code-block:: bash

        salt '*' bluetooth.nodiscover
    '''
    return _bt_set_discover_state(0)


def discoverable():
    '''
    Is this node discoverable

    CLI Example:

    .. code-block:: bash

        salt '*' bluetooth.discoverable
    '''
    if _bt_discover_state():
        return True
    else:
        return False
