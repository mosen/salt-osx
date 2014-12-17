# -*- coding: utf-8 -*-
'''
Get and set power management settings for different power sources on Mac OS X using the pmset(1) command line tool.
'''

import logging
import re
from string import strip, split
import salt.utils

log = logging.getLogger(__name__)

BOOLEAN_SETTINGS = ['womp', 'ring', 'autorestart', 'lidwake', 'acwake', 'lessbright', 'halfdim', 'sms',
                    'destroyfvkeyonstandby', 'autopoweroff']

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

