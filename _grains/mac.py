# -*- coding: utf-8 -*-
'''
    Mac Hardware Specific Grains.
    Partially inspired by [https://github.com/grahamgilbert/grahamgilbert-mac_facts], thanks grahamgilbert.
    These grains will be hardware related, while the osx grains will be operating system related. (just to keep
    it manageable).
'''


import logging
import salt.utils
import salt.modules.cmdmod
# import logging

log = logging.getLogger(__name__)

__virtualname__ = 'mac'

def __virtual__():
    if salt.utils.is_darwin():
        return __virtualname__
    else:
        return False

# Chicken and egg problem, SaltStack style
# __salt__ is already populated with grains by this stage.
cmdmod = {
    'cmd.run': salt.modules.cmdmod._run_quiet,
    # 'cmd.retcode': salt.modules.cmdmod._retcode_quiet,
    'cmd.run_all': salt.modules.cmdmod._run_all_quiet
}

def model():
    '''
    Get the (short) hardware model name. Eg. MacPro5,1
    '''
    # for k in __salt__.iterkeys():
    #     print k

    model = cmdmod['cmd.run']("sysctl -b hw.model")
    return {'model': model}


def has_wireless():
    '''
    Determine whether the mac has a wireless network interface.
    '''
    output = cmdmod['cmd.run']("networksetup -listallhardwareports | grep -E '(Wi-Fi|AirPort)' -A 1 | grep -o en.")
    return None if output == "" else {'mac_has_wireless':True}

