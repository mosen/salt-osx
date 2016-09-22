# -*- coding: utf-8 -*-
'''
Support for Directory Object query and manipulation via the DirectoryServices framework

:maintainer:    Mosen <mosen@github.com>
:maturity:      new
:depends:       objc
:platform:      darwin
'''


from __future__ import absolute_import
import logging
from pprint import pprint
from salt.exceptions import CommandExecutionError, SaltInvocationError

log = logging.getLogger(__name__)
has_imports = False

__virtualname__ = 'group'

try:
    import objc
    from OpenDirectory import ODSession, ODQuery, ODNode, \
        kODRecordTypeUsers, kODRecordTypeGroups, kODAttributeTypeRecordName, kODMatchContains, \
        kODAttributeTypeStandardOnly, kODMatchEqualTo, kODAttributeTypeUniqueID
    from Foundation import NSRunLoop, NSDefaultRunLoopMode, NSObject, NSDate
    has_imports = True
except ImportError:
    pass


def __virtual__():
    '''
    Module only loads on Darwin
    '''
    if not has_imports:
        return False, 'Open Directory only available on Darwin'
    else:
        return True

def _get_node(path):
    '''
    Get a reference to an ODNode instance given a path string eg. /LDAPv3/127.0.0.1
    '''
    session = ODSession.defaultSession()
    node, err = ODNode.nodeWithSession_name_error_(session, path, None)

    if err:
        raise CommandExecutionError(
            'cannot retrieve ODNode instance, reason: {}'.format(err)
        )

    return node

### group state compatibility

def add(name, gid=None, **kwargs):
    '''
    Add the specified group

    CLI Example:

    .. code-block:: bash

        salt '*' group.add foo 3456
    '''
    node = _get_node('/Local/Default')  # For now we will assume you want to alter the local directory.

    record, err = node.createRecordWithRecordType_name_attributes_error_(
        kODRecordTypeGroups,
        name,
        {},
        None
    )

    if err is not None:
        raise CommandExecutionError(
            'unable to create local directory group, reason: {}'.format(err.localizedDescription())
        )

    return True

def delete(name):
    '''
    Remove the named group

    CLI Example:

    .. code-block:: bash

        salt '*' group.delete foo
    '''
    group = _find_group('/Local/Default', name)
    if group is None or len(group) == 0:
        raise CommandExecutionError(
            'group {} does not exist'.format(name)
        )

    if len(group) > 1:
        raise CommandExecutionError(
            'Expected group name {} to match only a single group, matched: {}'.format(name, len(group))
        )

    group = group[0]

    deleted, err = group.deleteRecordAndReturnError_(None)
    if err:
        raise CommandExecutionError(
            'Unable to delete the group, reason: {}'.format(err.localizedDescription())
        )

    return deleted


def nodes():
    '''
    Get a list of registered nodes eg. /Local/Default

    CLI Example::

        salt '*' opendirectory.nodes
    '''
    session = ODSession.defaultSession()
    names, err = session.nodeNamesAndReturnError_(None)

    if err is not None:
        log.error(err)
        return None

    # The method returns with a tuple so it is converted to a list here.
    return list(names)


def search(path, searchValue):
    '''
    List records that match the given query.
    '''
    node = _get_node(path)

    if not node:
        log.error('Query not possible, cannot get reference to node at path: {}'.format(path))
        return None

    query, err = ODQuery.alloc().initWithNode_forRecordTypes_attribute_matchType_queryValues_returnAttributes_maximumResults_error_(
        node,
        kODRecordTypeGroups,
        kODAttributeTypeRecordName,
        kODMatchContains,
        searchValue,
        kODAttributeTypeStandardOnly,
        0,
        None
    )

    if err:
        log.error('Failed to construct query: {}'.format(err))
        return None

    ODQueryDelegate = objc.protocolNamed('ODQueryDelegate')

    class QueryDelegate(NSObject, ODQueryDelegate):
        def query_foundResults_error_(self, inQuery, inResults, inError):
            log.error('FOUND RESULTS')

    qd = QueryDelegate()
    query.setDelegate_(qd)
    query.scheduleInRunLoop_forMode_(NSRunLoop.currentRunLoop(), NSDefaultRunLoopMode)


def _format_odrecord_group(record):
    '''
    Format an ODRecord object representing a Group into a python dict.

    :param record:
    :return:
    '''
    pass

def _find_group(path, groupName):
    '''
    Search for groups using the given criteria.

    CLI Example::

        salt '*' group._find_group <path> <name>
    '''
    node = _get_node(path)

    if not node:
        raise SaltInvocationError(
            'directory services query not possible, cannot get reference to node at path: {}'.format(path)
        )

    query, err = ODQuery.alloc().initWithNode_forRecordTypes_attribute_matchType_queryValues_returnAttributes_maximumResults_error_(
        node,
        kODRecordTypeGroups,
        kODAttributeTypeRecordName,
        kODMatchEqualTo,
        groupName,
        kODAttributeTypeStandardOnly,
        1,
        None
    )

    if err:
        raise SaltInvocationError(
            'Failed to construct query: {}'.format(err)
        )

    results, err = query.resultsAllowingPartial_error_(False, None)

    if err:
        raise SaltInvocationError(
            'Failed to query opendirectory: {}'.format(err)
        )

    return results


def _find_gid(path, gid):
    '''
    Search for groups using the given criteria.

    CLI Example::

        salt '*' group._find_gid <path> <gid>
    '''
    node = _get_node(path)

    if not node:
        raise SaltInvocationError(
            'directory services query not possible, cannot get reference to node at path: {}'.format(path)
        )

    query, err = ODQuery.alloc().initWithNode_forRecordTypes_attribute_matchType_queryValues_returnAttributes_maximumResults_error_(
        node,
        kODRecordTypeGroups,
        kODAttributeTypeUniqueID,
        kODMatchEqualTo,
        gid,
        kODAttributeTypeStandardOnly,
        1,
        None
    )

    if err:
        raise SaltInvocationError(
            'Failed to construct query: {}'.format(err)
        )

    results, err = query.resultsAllowingPartial_error_(False, None)

    if err:
        raise SaltInvocationError(
            'Failed to query opendirectory: {}'.format(err)
        )

    return results
