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


def detailed_users():
    return {'macos_users_detailed': {u['name']: u for u in _get_users()}}


def _get_users():
    result = cmdmod['cmd.run']('dscacheutil -q user')
	# Example output:
	# name: _reportmemoryexception
	# password: *
	# uid: 269
	# gid: 269
	# dir: /var/db/reportmemoryexception
	# shell: /usr/bin/false
	# gecos: ReportMemoryException
    pattern = (
        r'(?m)'
        r'^name: (?P<name>.*?)\n'
        r'^.*?\n'
        r'^uid: (?P<uid>\d+)\n'
        r'^gid: (?P<gid>\d+)\n'
        r'^dir: (?P<dir>.*?)\n'
        r'^shell: (?P<shell>.*?)\n'
        r'^gecos: (?P<gecos>.*?)\n$')
    return (m.groupdict() for m in re.finditer(pattern, result))


if __name__ == "__main__":
    print(users())
