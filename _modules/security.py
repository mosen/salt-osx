# -*- coding: utf-8 -*-
'''
Security Module
===============

Manage keychain items via the `security` command.

:maintainer:    Mosen <mosen@github.com>
:maturity:      new
:depends:       objc
:platform:      darwin
'''

import logging
import salt.utils
import salt.exceptions
import re

log = logging.getLogger(__name__)

__virtualname__ = 'security'


def __virtual__():
    return __virtualname__ if salt.utils.platform.is_darwin() else False


def _parse_attr_line(line):
    return ('', '')

def _parse_value_line(line):
    key, value = line.split(':')
    return key, value

def _parse_cert_line(line):
    '''Parse attribute line from security stdout'''
    if re.match('^\s{4}', line):
        return None, None
    else:
        return _parse_value_line(line)


def _parse_cert_attributes(stdout):
    '''Parse certificate attributes from stdout of security tool. Assumes SHA-1 hash is included'''
    outlines = stdout.splitlines()
    attrs = dict()

    for line in outlines:
        k, v = _parse_cert_line(line)
        if k is not None:
            attrs[k] = v

    return attrs

def dump_certificate(name):
    '''
    Dump a certificate in PEM format.

    name
        The certificate name

    CLI Example:

    .. code-block:: bash

        salt '*' security.dump_certificate CA1
    '''
    result = __salt__['cmd.run_all'](
        '/usr/bin/security find-certificate -c "{0}" -p'.format(name)
    )

    if result['retcode'] != 0:
        return None  # No certificate found
    else:
        return result['stdout']


def find_certificate(name):
    '''
    Find a certificate item by name

    name
        The certificate name


    CLI Example:

    .. code-block:: bash

        salt '*' security.find_certificate CA1
    '''
    result = __salt__['cmd.run_all'](
        '/usr/bin/security find-certificate -c "{0}" -Z'.format(name)
    )

    if result['retcode'] != 0:
        return None  # No certificate found

    return _parse_cert_attributes(result['stdout'])
