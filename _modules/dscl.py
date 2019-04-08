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
_DSCL_PATH = '/usr/bin/dscl'
_DSCACHEUTIL = '/usr/bin/dscacheutil'

def __virtual__():
    return __virtualname__ if salt.utils.platform.is_darwin() else False


def flushcache():
    '''
    Flush the Directory Service cache
    :return:
    '''
    __salt__['cmd.run']('{0} -flushcache'.format(_DSCACHEUTIL))


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


def read(datasource, path, key=None, **kwargs):
    '''
    Read an attribute (or all attributes) of a directory record.
    Returns a dict containing a keys and values. If either the specified record or attribute did not exist, returns None

    datasource
        The datasource to search. Usually either '.' (for the local directory) or '/Search'
        for all directory services in the search path.

    path
        The path of the resource eg. /Users/admin.
        If the path is invalid, this will return False

    key : None
        The attribute to get, the default (None) retrieves all attributes.
        If the key doesnt exist as an attribute of the record, this will return an empty dict

    Keyword arguments:

    format : 'string' or 'plist'
        The return format for the command, string is Attribute: Value, and plist returns a property list with one
        entry for the requested key

    parse : true or false
        If the format was 'string', attempt to parse attributes into a dictionary, defaults to True

    CLI Example:

    .. code-block:: bash

        salt '*' dscl.read . /Users/admin naprivs
    '''
    cmdargs = [_DSCL_PATH]

    if kwargs.get('format') == 'plist':
        cmdargs.append('-plist')

    if datasource:
        cmdargs.append(datasource)
    else:
        cmdargs.append('.')

    cmdargs.append('read')
    cmdargs.append(path)

    if key is not None:
        cmdargs.append(key)

    result = __salt__['cmd.run_all'](' '.join(cmdargs))

    if result['retcode'] != 0:
        log.warning('Attempted to read a record that doesnt exist: {0}'.format(path))
        return None

    if re.search('No such key', result['stderr']):
        log.warning('Attempted to read a record attribute that doesnt exist: {0}'.format(key))
        return None

    if kwargs.get('format', 'string') == 'string' and kwargs.get('parse', True) is True:
        ret = {}
        k = None

        # If not using plist format, attribute values can be on the same line or following line
        for line in result['stdout'].splitlines():
            if k is not None:  # Push value for current multi-line property
                ret[k] = line
                k = None
            elif line[-1] == ':':  # This line describes a property
                k = line[:-1]
            else:  # This line contains a property name and value
                parts = line.split(': ')
                ret[parts[0]] = parts[1]

        return ret
    else:
        return result['stdout']


def delete(datasource, path, key=None, value=None):
    '''
    Delete a record, record attribute, or a single value from a record attribute.

    datasource
        The datasource to search. Usually either '.' (for the local directory) or '/Search'
        for all directory services in the search path.

    path
        The path of the resource

    key : None
        The attribute of the resource (specified by path) to delete. Leave this empty to delete the entire resource

    value : None
        The value to delete from the specified attribute, if removing items from a list type attribute.
    '''
    if key is not None and len(key) == 0:
        log.warning('Attempted to delete a key with zero length string, this could remove the entire record. Aborting')
        return False

    if value is not None and len(value) == 0:
        log.warning('Attempted to delete a value with zero length string, this could remove the entire key. Aborting')
        return False

    result = __salt__['cmd.run_all'](
        '/usr/bin/dscl {0} delete {1} {2} {3}'.format(datasource, path, key, value)
    )

    if result['retcode'] != 0:
        log.warning('Attempted to delete a record, key, or attribute that doesnt exist: {0}:{1}:{2}'.format(path, key, value))

    return True
