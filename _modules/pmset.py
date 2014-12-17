# -*- coding: utf-8 -*-
'''
Get and set power management settings for different power sources on Mac OS X using the pmset(1) command line tool.
'''

import logging
import re
from string import strip, split
import salt.utils

log = logging.getLogger(__name__)

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
            property = split(strip(line))
            if len(property) == 2:
                current[property[0]] = property[1]

    if current != dict():
        settings[source] = current

    return settings

