# -*- coding: utf-8 -*-
'''
This module exists specifically to parse battery information, if we determine that the minion is running on a portable
machine (In this case a MacBook)
'''

import salt.utils
import salt.modules.cmdmod
import logging
import re

log = logging.getLogger(__name__)

__virtualname__ = 'mac_battery'

def __virtual__():

    if salt.utils.is_darwin():
        if re.search('Book', salt.modules.cmdmod._run_quiet('sysctl -b hw.model')):
            return __virtualname__
        else:
            return False
    else:
        return False

def grains():
    """
    Populate grain information with all MacBook battery information.
    """
    pass
    # ioreg -a -r -c 'AppleSmartBattery'
    # parse plist dict back to grains

