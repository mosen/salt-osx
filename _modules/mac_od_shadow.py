# -*- coding: utf-8 -*-
'''
Support for password and password policy modification via the DirectoryServices framework.

:maintainer:    Mosen <mosen@github.com>
:maturity:      new
:depends:       objc
:platform:      darwin
'''

from __future__ import absolute_import
import logging
from salt.exceptions import CommandExecutionError, SaltInvocationError
import salt.utils

log = logging.getLogger(__name__)
has_imports = False

__virtualname__ = 'shadow'

try:
    import objc
    from OpenDirectory import ODSession, ODQuery, ODNode, \
        kODRecordTypeUsers, kODRecordTypeGroups, kODAttributeTypeRecordName, kODMatchContains, \
        kODAttributeTypeStandardOnly, kODMatchEqualTo, kODMatchAny, \
        kODAttributeTypeAllTypes, kODAttributeTypeUniqueID, kODAttributeTypePrimaryGroupID, kODAttributeTypeNFSHomeDirectory, \
        kODAttributeTypeUserShell, kODAttributeTypeFullName, kODAttributeTypeGUID, kODAttributeTypeRecordName
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


def _get_account_policy(name):
    '''
    Get the entire accountPolicy and return it as a dictionary. For use by this
    module only

    :param str name: The user name

    :return: a dictionary containing all values for the accountPolicy
    :rtype: dict

    :raises: CommandExecutionError on user not found or any other unknown error
    '''
    user = _find_user('/Local/Default', name)
    if user is None:
        return None

    policies, err = user.accountPoliciesAndReturnError_(None)
    if err is not None:
        raise SaltInvocationError(
            'failed to retrieve account policies for user: {}, reason: {}'.format(name, err.localizedDescription())
        )

    return policies


def info(name):
    '''
    Return information for the specified user

    :param str name: the username

    :return: A dictionary containing the user's shadow information
    :rtype: dict

    CLI Example:

    .. code-block:: bash

        salt '*' shadow.info admin
    '''
    user = _find_user('/Local/Default', name)
    if user is None:
        return None

    policies = _get_account_policy(name)
    return policies


def del_password(name):
    '''
    Deletes the account password

    :param str name: The user name of the account

    :return: True if successful, otherwise False
    :rtype: bool

    :raises: CommandExecutionError on user not found or any other unknown error

    CLI Example:

    .. code-block:: bash

        salt '*' shadow.del_password username
    '''
    user = _find_user('/Local/Default', name)
    if user is None:
        raise CommandExecutionError(
            'could not find user to remove password: {}'.format(name)
        )

    didChange, err = user.changePassword_toPassword_error_(None, None, None)
    if err is not None:
        raise CommandExecutionError(
            'could not remove password on user: {}, reason: {}'.format(name, err.localizedDescription())
        )

    return didChange


def set_password(name, password):
    '''
    Set the password for a named user (insecure, the password will be in the
    process list while the command is running)

    :param str name: The name of the local user, which is assumed to be in the
    local directory service

    :param str password: The plaintext password to set

    :return: True if successful, otherwise False
    :rtype: bool

    :raises: CommandExecutionError on user not found or any other unknown error

    CLI Example:

    .. code-block:: bash

        salt '*' mac_shadow.set_password macuser macpassword
    '''
    user = _find_user('/Local/Default', name)
    if user is None:
        raise CommandExecutionError(
            'could not find user to remove password: {}'.format(name)
        )

    didChange, err = user.changePassword_toPassword_error_(None, password, None)
    if err is not None:
        raise CommandExecutionError(
            'could not remove password on user: {}, reason: {}'.format(name, err.localizedDescription())
        )

    return didChange


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
    Find a user object in the local directory by their username.
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

    if results is None or len(results) == 0:
        return None

    if len(results) > 1:
        raise CommandExecutionError(
            'Expected user name {} to match only a single user, matched: {} result(s)'.format(userName, len(user))
        )

    return results[0]

