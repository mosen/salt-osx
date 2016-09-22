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


def add(name, gid=None, **kwargs):
    '''
    Add the specified group

    CLI Example:

    .. code-block:: bash

        salt '*' group.add foo 3456
    '''
    node = _get_node('/Local/Default')  # For now we will assume you want to alter the local directory.

    attributes = {}
    if gid is not None:
        attributes['PrimaryGroupID'] = [gid]

    record, err = node.createRecordWithRecordType_name_attributes_error_(
        kODRecordTypeGroups,
        name,
        attributes,
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


def adduser(group, name):
    '''
    Add a user in the group.

    CLI Example:

    .. code-block:: bash

         salt '*' group.adduser foo bar

    Verifies if a valid username 'bar' as a member of an existing group 'foo',
    if not then adds it.
    '''
    groupObject = _find_group('/Local/Default', name)
    if groupObject is None or len(groupObject) == 0:
        raise CommandExecutionError(
            'group {} does not exist'.format(name)
        )

    if len(groupObject) > 1:
        raise CommandExecutionError(
            'Expected group name {} to match only a single group, matched: {}'.format(group, len(groupObject))
        )

    groupObject = groupObject[0]

    user = _find_user('/Local/Default', name)
    if user is None or len(user) == 0:
        raise CommandExecutionError(
            'user {} does not exist'.format(name)
        )

    if len(user) > 1:
        raise CommandExecutionError(
            'Expected group name {} to match only a single group, matched: {}'.format(name, len(user))
        )

    user = user[0]

    added, err = groupObject.addMemberRecord_error_(
        user, None
    )
    if err:
        raise CommandExecutionError(
            'Unable to add member {} to group {}, reason: {}'.format(name, group, err.localizedDescription())
        )

    return added


def deluser(group, name):
    '''
    Remove a user from the group

    .. versionadded:: 2016.3.0

    CLI Example:

    .. code-block:: bash

         salt '*' group.deluser foo bar

    Removes a member user 'bar' from a group 'foo'. If group is not present
    then returns True.
    '''
    groupObject = _find_group('/Search', name)
    if groupObject is None or len(groupObject) == 0:
        raise CommandExecutionError(
            'group {} does not exist'.format(name)
        )

    if len(groupObject) > 1:
        raise CommandExecutionError(
            'Expected group name {} to match only a single group, matched: {}'.format(group, len(groupObject))
        )

    groupObject = groupObject[0]

    user = _find_user('/Local/Default', name)
    if user is None or len(user) == 0:
        raise CommandExecutionError(
            'user {} does not exist'.format(name)
        )

    if len(user) > 1:
        raise CommandExecutionError(
            'Expected group name {} to match only a single group, matched: {}'.format(name, len(user))
        )

    user = user[0]

    removed, err = groupObject.removeMemberRecord_error_(
        user, None
    )
    if err:
        raise CommandExecutionError(
            'Unable to remove member {} from group {}, reason: {}'.format(name, group, err.localizedDescription())
        )

    return removed


def info(name):
    '''
    Return information about a group

    CLI Example:

    .. code-block:: bash

        salt '*' group.info foo
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
    attrs, err = group.recordDetailsForAttributes_error_(None, None)

    if err is not None:
        raise CommandExecutionError(
            'Could not get attributes for group {}, reason: {}'.format(name, err.localizedDescription())
        )

    return _format_info(attrs)


def _format_info(data):
    '''
    Return formatted information in a pretty way.
    '''
    attrs = {}

    for k, v in data.iteritems():
        attrs[k] = list(v)

    return attrs


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
    Find a group object in the local directory by its unique id (gid)
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


def _find_user(path, userName):
    '''
    Find a user object in the local directory by their username
    '''
    node = _get_node(path)

    if not node:
        raise SaltInvocationError(
            'directory services query not possible, cannot get reference to node at path: {}'.format(path)
        )

    query, err = ODQuery.alloc().initWithNode_forRecordTypes_attribute_matchType_queryValues_returnAttributes_maximumResults_error_(
        node,
        kODRecordTypeUsers,
        kODAttributeTypeRecordName,
        kODMatchEqualTo,
        userName,
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