"""Grain to get user accounts on a macOS system."""


import logging
import re

import salt.modules.cmdmod
import salt.utils.platform


log = logging.getLogger(__name__)

__virtualname__ = 'users'


def __virtual__():
    if salt.utils.platform.is_darwin():
        return __virtualname__
    else:
        return False

# Chicken and egg problem, SaltStack style
# __salt__ is already populated with grains by this stage.
cmdmod = {
    'cmd.run': salt.modules.cmdmod._run_quiet,
}


def users():
    return {'macos_users': [u for u in _get_users() if not u.startswith('_')]}


def _get_users():
    return cmdmod['cmd.run']('dscl . list /Users').splitlines()
