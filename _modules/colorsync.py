"""
Retrieve information about Apple's ColorSync settings and profiles

:maintainer:    Mosen <mosen@github.com>
:maturity:      new
:depends:       objc,Foundation,Cocoa
:platform:      darwin
"""

__virtualname__ = 'colorsync'

import logging

log = logging.getLogger(__name__)

def devices():
    '''
    List ColorSync Devices
    :return:
    '''
    device_list = __salt__['cmd.run']('defaults -currentHost read NSGlobalDomain com.apple.ColorSync.Devices')
