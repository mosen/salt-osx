# -*- coding: utf-8 -*-
'''
Query the local directory service and/or directories on the search path using ``dscl`` (Mac OS X only).
This is just a simple wrapper which services other execution modules.
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

    return {'matches': [line.split("\t\t")[0] for line in output if re.search("\w\t\t\w", line)]}


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

    return {matches.group(1): matches.group(2) for matches in
            [re.match('(\S*)\s*(.*)', line) for line in output.splitlines()]}


def create(datasource, path, key, value):
    '''
    Set the value of an attribute, given the path to a directory record.

    datasource
        The datasource to search. Usually either '.' (for the local directory) or '/Search'
        for all directory services in the search path.

    path
        The path of the resource eg. /Users/admin

    key
        The attribute to set

    value
        The value to set for that attribute

    CLI Example:

    .. code-block:: bash

        salt '*' dscl.create . /Users/admin RealName 'Joey Joe Joe'
    '''
    status = __salt__['cmd.retcode'](
        '/usr/bin/dscl {0} create {1} {2} {3}'.format(datasource, path, key, value)
    )

    return True if status == 0 else False


def read(datasource, path, key=None):
    '''
    Read an attribute (or all attributes) of a directory record.
    Returns a dict containing a keys and values.

    datasource
        The datasource to search. Usually either '.' (for the local directory) or '/Search'
        for all directory services in the search path.

    path
        The path of the resource eg. /Users/admin.
        If the path is invalid, this will return False

    key : None
        The attribute to get, the default (None) retrieves all attributes.
        If the key doesnt exist as an attribute of the record, this will return an empty dict

    CLI Example:

    .. code-block:: bash

        salt '*' dscl.read . /Users/admin naprivs
    '''
    result = __salt__['cmd.run_all'](
        '/usr/bin/dscl {0} read {1} {2}'.format(datasource, path, key)
    )

    if result['retcode'] != 0:
        log.warning('Attempted to read a record that doesnt exist: {0}'.format(path))
        return False

    if re.search('No such key', result['stderr']):
        log.warning('Attempted to read a record attribute that doesnt exist: {0}'.format(key))
        return {}

    return {parts[0]: parts[1] for parts in [line.split(': ') for line in result['stdout'].splitlines()]}