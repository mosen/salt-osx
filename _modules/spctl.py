# -*- coding: utf-8 -*-
'''
manage SecAssessment security policy aka "GateKeeper".

:maintainer:    Mosen <mosen@github.com>
:maturity:      beta
:platform:      darwin
'''

import logging
import salt.utils

log = logging.getLogger(__name__)

__virtualname__ = 'spctl'


def __virtual__():
    '''
    Only load module if we are running on OS X.
    '''
    return __virtualname__ if salt.utils.is_darwin() else False


def enabled():
    '''
    Determine whether the SecAssessment policy subsystem is enabled.

    CLI Example:

    .. code-block:: bash

        salt '*' spctl.enabled
    '''
    status = __salt__['cmd.retcode']('/usr/sbin/spctl --status')
    return True if status == 0 else False


def enable():
    '''
    Enable the SecAssessment policy subsystem.

    CLI Example:

    .. code-block:: bash

        salt '*' spctl.enable
    '''
    status = __salt__['cmd.retcode']('/usr/sbin/spctl --master-enable')
    return True if status == 0 else False


def disable():
    '''
    Disable the SecAssessment policy subsystem.

    CLI Example:

    .. code-block:: bash

        salt '*' spctl.disable
    '''
    status = __salt__['cmd.retcode']('/usr/sbin/spctl --master-disable')
    return True if status == 0 else False