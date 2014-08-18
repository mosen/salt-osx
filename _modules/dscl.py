# -*- coding: utf-8 -*-
'''
Query the local directory service and/or directories on the search path using 'dscl' (Mac OS X only)
'''

import logging
import re
import salt.utils

log = logging.getLogger(__name__)

__virtualname__ = 'dscl'

def __virtual__():
    return __virtualname__ if salt.utils.is_darwin() else False

def search(datasource, path, key, value):
    '''
    Search for a directory record with matching attribute value.
    Returns a dict containing a 'matches' list of record names which were returned from the search.

    datasource
        The datasource to search. Usually either '.' (for the local directory) or '/Search'
        for all directory services in the search path.

    path
        The path in which to search eg. /Users for user records.

    key
        The attribute to search

    value
        The pattern to match

    CLI Example:

    .. code-block:: bash

        salt '*' dscl.search . /Users UserShell /bin/bash
    '''
    output = __salt__['cmd.run'](
        '/usr/bin/dscl {0} -search {1} {2} "{3}"'.format(datasource, path, key, value.replace('"', '\"'))
    ).splitlines()

    if len(output) == 0:
        return None

    return { 'matches': [line.split("\t\t")[0] for line in output if re.search("\w\t\t\w", line)] }

def list(datasource, path, key=''):
    '''
    List records in the given path. You can optionally supply an attribute name to
    retrieve with each record.

    Returns a dict containing keys of records, and values for the requested attribute (if any was supplied)

    datasource
        The datasource to search. Usually either '.' (for the local directory) or '/Search'
        for all directory services in the search path.

    path
        The path in which to search eg. /Users for user records.

    key
        The attribute to fetch for each record

    CLI Example:

    .. code-block:: bash

        salt '*' dscl.list . /Users RealName
    '''
    output = __salt__['cmd.run'](
        '/usr/bin/dscl {0} list {1} {2}'.format(datasource, path, key)
    )

    return {matches.group(1):matches.group(2) for matches in [re.match('(\S*)\s*(.*)', line) for line in output.splitlines()]}
