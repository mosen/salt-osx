# -*- coding: utf-8 -*-
'''
Get and set power management settings for different power sources on Mac OS X using the pmset(1) command line tool.
'''

import logging
import re
from string import strip, split, join, lower
import salt.utils
import salt.exceptions

log = logging.getLogger(__name__)

POWER_SOURCES = ['ac', 'battery']  # ups not supported
POWER_SWITCHES = {'ac': '-c', 'battery': '-b'}
BOOLEAN_SETTINGS = ['womp', 'ring', 'autorestart', 'lidwake', 'acwake', 'lessbright', 'halfdim', 'sms',
                    'ttyskeepawake', 'destroyfvkeyonstandby', 'autopoweroff']
VALID_SETTINGS = ['displaysleep', 'disksleep', 'sleep', 'womp', 'ring', 'autorestart', 'lidwake', 'acwake',
                  'lessbright', 'halfdim', 'sms', 'ttyskeepawake', 'destroyfvkeyonstandby', 'autopoweroff',
                  'autopoweroffdelay']

__virtualname__ = 'pmset'


def __virtual__():
    return __virtualname__ if salt.utils.is_darwin() else False


def list_settings():
    '''
    Get list of current settings for all power sources.
    Returns a list of dicts.

    CLI Example:

    .. code-block:: bash

        salt '*' pmset.list_settings
    '''
    output = __salt__['cmd.run']('/usr/bin/pmset -g custom').splitlines()

    if len(output) == 0:
        return None

    settings = dict()
    current = dict()
    source = None

    for line in output:
        if re.search("^AC Power:", line):
            if source is not None:
                settings[source] = current
                current = dict()
            source = "ac"
        elif re.search("^Battery Power:", line):
            if source is not None:
                settings[source] = current
                current = dict()
            source = "battery"
        else:
            kv = split(strip(line))
            if len(kv) == 2:
                if kv[0] in BOOLEAN_SETTINGS:
                    current[kv[0]] = True if kv[1] == "1" else False
                else:
                    current[kv[0]] = kv[1]

    if current != dict():
        settings[source] = current

    return settings


def set_settings(name, **kwargs):
    '''
    Set power management settings for the named power source.
    Parameter names are exactly as in pmset. A value of zero means never sleep for
    sleep values.

    name
        The power source that the settings apply to, one of: "ac" or "battery"

    displaysleep
        Display sleep timer

    disksleep
        Disk sleep timer

    sleep
        Computer sleep timer

    womp
        Wake on ethernet magic packet

    ring
        Wake on modem ring

    autorestart
        Automatic restart on power loss

    lidwake
        Wake the machine when laptop lid is opened

    acwake
        Wake the machine when power source is changed

    lessbright
        slightly turn down display brightness when switching to this power source

    halfdim
        display sleep will use an intermediate half-brightness state between full brightness and fully off

    sms
        use Sudden Motion Sensor to park disk heads on sudden changes in G force

    ttyskeepawake
        prevent idle system sleep when any tty (e.g. remote login session) is 'active'.

    destroyfvkeyonstandby
        Destroy File Vault Key when going to standby mode.

    autopoweroff

    autopoweroffdelay

    CLI Example:

    .. code-block:: bash

        salt '*' pmset.set_settings ac sleep=120
    '''
    if name not in POWER_SOURCES:
        raise salt.exceptions.SaltInvocationError(
            'Invalid power source given: {}'.format(name)
        )

    valid_settings = {k: str(v) for k, v in kwargs.iteritems() if k in VALID_SETTINGS}
    normal_settings = {}

    for k, v in valid_settings.iteritems():
        if k in BOOLEAN_SETTINGS:
            normal_settings[k] = '1' if lower(v) == 'true' or v == '1' else '0'
        else:
            normal_settings[k] = v

    args = join([join(pair, ' ') for pair in normal_settings.iteritems()], ' ')

    result = __salt__['cmd.run_all'](
        '/usr/bin/pmset {0} {1}'.format(POWER_SWITCHES[name], args)
    )

    return result['retcode']