# -*- coding: utf-8 -*-
'''
    OSX/Darwin Specific Grains.

    Grains that relate to the operating system/platform
'''
import salt.utils
import salt.modules.cmdmod
import logging

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

def filevault_enabled():
    '''Is FileVault enabled?'''
    fv_status = cmdmod['cmd.run']('fdesetup status')
    grains = {}

    if fv_status == 'FileVault is On.':
        grains['filevault_enabled'] = True
    else:
        grains['filevault_enabled'] = False

    return grains