# -*- coding: utf-8 -*-
'''
Support for local user manipulation via the DirectoryServices framework

:maintainer:    Mosen <mosen@github.com>
:maturity:      new
:depends:       objc
:platform:      darwin
'''

from __future__ import absolute_import
import logging
from salt.exceptions import CommandExecutionError, SaltInvocationError

log = logging.getLogger(__name__)
has_imports = False

__virtualname__ = 'user'

try:
    import objc
    from OpenDirectory import ODSession, ODQuery, ODNode, \
        kODRecordTypeUsers, kODRecordTypeGroups, kODAttributeTypeRecordName, kODMatchContains, \
        kODAttributeTypeStandardOnly, kODMatchEqualTo, kODMatchAny, \
        kODAttributeTypeAllTypes, kODAttributeTypeUniqueID, kODAttributeTypePrimaryGroupID, kODAttributeTypeNFSHomeDirectory, \
        kODAttributeTypeUserShell, kODAttributeTypeFullName, kODAttributeTypeGUID
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
        return __virtualname__


def add(name,
        uid=None,
        gid=None,
        groups=None,
        home=None,
        shell=None,
        fullname=None,
        createhome=True,
        **kwargs):
    '''
    Add a user to the minion

    CLI Example:

    .. code-block:: bash

        salt '*' user.add name <uid> <gid> <groups> <home> <shell>
    '''
    node = _get_node('/Local/Default')  # For now we will assume you want to alter the local directory.
    attributes = {}

    if uid is not None:
        attributes[kODAttributeTypeUniqueID] = [uid]
    #
    # if gid is not None:
    #
    #     attributes[kODAttributeTypePrimaryGroupID] = [20]  # gid 20 == 'staff', the default group
    # else:
    #     attributes[kODAttributeTypePrimaryGroupID] = [gid]

    if home is None:
        attributes[kODAttributeTypeNFSHomeDirectory] = ['/Users/{0}'.format(name)]
    else:
        attributes[kODAttributeTypeNFSHomeDirectory] = [home]

    if shell is None:
        attributes[kODAttributeTypeUserShell] = ['/bin/bash']
    else:
        attributes[kODAttributeTypeUserShell] = [shell]

    if fullname is not None:
        attributes[kODAttributeTypeFullName] = [fullname]

    record, err = node.createRecordWithRecordType_name_attributes_error_(
        kODRecordTypeUsers,
        name,
        attributes,
        None
    )

    if err is not None:
        raise CommandExecutionError(
            'unable to create local directory user, reason: {}'.format(err.localizedDescription())
        )

    synced, err = record.synchronizeAndReturnError_(None)
    if err is not None:
        raise CommandExecutionError(
            'error retrieving newly updated user record, reason: {}'.format(err.localizedDescription())
        )

    guids, err = record.valuesForAttribute_error_(kODAttributeTypeGUID, None)
    if err is not None:
        raise CommandExecutionError(
            'error reading guid of user record, reason: {}'.format(err.localizedDescription())
        )

    if guids is None:
        raise CommandExecutionError(
            'expected 1 guid for newly created user, got none'
        )

    if len(guids) != 1:
        raise CommandExecutionError(
            'expected 1 guid for newly created user, got {} guid(s)'.format(len(guids))
        )

    guid = guids[0]

    # TODO: createhome
    # TODO: group membership

    return True


def delete(name, remove=False, force=False):
    '''
    Remove a user from the minion

    CLI Example:

    .. code-block:: bash

        salt '*' user.delete name remove=True force=True
    '''
    # force is added for compatibility with user.absent state function
    if force:
        log.warn('force option is unsupported on MacOS, ignoring')

    # remove home directory from filesystem
    # if remove:
    #     __salt__['file.remove'](info(name)['home'])

    # Remove from any groups other than primary group. Needs to be done since
    # group membership is managed separately from users and an entry for the
    # user will persist even after the user is removed.
    # chgroups(name, ())
    user = _find_user('/Local/Default', name)
    if user is None or len(user) == 0:
        raise CommandExecutionError(
            'user {} does not exist'.format(name)
        )

    if len(user) > 1:
        raise CommandExecutionError(
            'Expected user name {} to match only a single user, matched: {}'.format(name, len(user))
        )

    user = user[0]

    deleted, err = user.deleteRecordAndReturnError_(None)
    if err:
        raise CommandExecutionError(
            'Unable to delete the user, reason: {}'.format(err.localizedDescription())
        )

    return deleted



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

