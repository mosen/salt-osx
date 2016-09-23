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
import salt.utils

log = logging.getLogger(__name__)
has_imports = False

__virtualname__ = 'user'

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
    setattrs = {}

    if uid is not None:
        setattrs[kODAttributeTypeUniqueID] = uid

    if gid is None:
        setattrs[kODAttributeTypePrimaryGroupID] = 20  # gid 20 == 'staff', the default group
    else:
        setattrs[kODAttributeTypePrimaryGroupID] = gid

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

    for k, v in setattrs.items():
        setted, err = record.setValue_forAttribute_error_(v, k, None)
        if err is not None:
            log.error('failed to set attribute {} on user {}, reason: {}'.format(k, name, err.localizedDescription()))

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

    if createhome:
        __salt__['file.mkdir'](home, user=uid, group=gid)
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

    user = _find_user('/Local/Default', name)
    if user is None:
        raise CommandExecutionError(
            'user {} does not exist'.format(name)
        )

    # Remove from any groups other than primary group. Needs to be done since
    # group membership is managed separately from users and an entry for the
    # user will persist even after the user is removed.
    # chgroups(name, ())



    # remove home directory from filesystem
    if remove:
        # TODO: Ensure that the path described is local
        __salt__['file.remove'](user[kODAttributeTypeNFSHomeDirectory])

    deleted, err = user.deleteRecordAndReturnError_(None)
    if err:
        raise CommandExecutionError(
            'Unable to delete the user, reason: {}'.format(err.localizedDescription())
        )

    return deleted


def _format_info(data):
    '''
    Return formatted information in a pretty way.
    '''
    attrs = {}

    for k, v in data.iteritems():
        attrs[k] = list(v)

    # TODO: Normalise OD attributes into unix compatible results

    return attrs


def getent(refresh=False):
    '''
    Return info on all users

    CLI Example:

    .. code-block:: bash

        salt '*' group.getent
    '''
    if 'user.getent' in __context__ and not refresh:
        return __context__['user.getent']

    node = _get_node('/Local/Default')
    query, err = ODQuery.alloc().initWithNode_forRecordTypes_attribute_matchType_queryValues_returnAttributes_maximumResults_error_(
        node,
        kODRecordTypeUsers,
        kODAttributeTypeAllTypes,
        kODMatchAny,
        None,
        kODAttributeTypeStandardOnly,
        200,  # TODO: hard coded limit bad
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

    userAttrs = []
    for result in results:
        attrs, err = result.recordDetailsForAttributes_error_(None, None)
        userAttrs.append(attrs)

    return [_format_info(attrs) for attrs in userAttrs]


def chuid(name, uid):
    '''
    Change the uid for a named user

    CLI Example:

    .. code-block:: bash

        salt '*' user.chuid foo 4376
    '''
    if not isinstance(uid, int):
        raise SaltInvocationError('uid must be an integer')

    return _update_attribute(name, kODAttributeTypeUniqueID, uid)


def chgid(name, gid):
    '''
    Change the default group of the user

    CLI Example:

    .. code-block:: bash

        salt '*' user.chgid foo 4376
    '''
    if not isinstance(gid, int):
        raise SaltInvocationError('gid must be an integer')

    return _update_attribute(name, kODAttributeTypePrimaryGroupID, uid)


def chshell(name, shell):
    '''
    Change the default shell of the user

    CLI Example:

    .. code-block:: bash

        salt '*' user.chshell foo /bin/zsh
    '''
    return _update_attribute(name, kODAttributeTypeUserShell, uid)


def chhome(name, home, **kwargs):
    '''
    Change the home directory of the user

    CLI Example:

    .. code-block:: bash

        salt '*' user.chhome foo /Users/foo
    '''
    kwargs = salt.utils.clean_kwargs(**kwargs)
    persist = kwargs.pop('persist', False)
    if kwargs:
        salt.utils.invalid_kwargs(kwargs)
    if persist:
        log.info('Ignoring unsupported \'persist\' argument to user.chhome')

    return _update_attribute(name, kODAttributeTypeNFSHomeDirectory, home)


def chfullname(name, fullname):
    '''
    Change the user's Full Name

    CLI Example:

    .. code-block:: bash

        salt '*' user.chfullname foo 'Foo Bar'
    '''
    # if isinstance(fullname, string_types):
    #     fullname = _sdecode(fullname)

    return _update_attribute(name, kODAttributeTypeFullName, fullname)


# TODO: chgroups


def info(name):
    '''
    Return user information

    CLI Example:

    .. code-block:: bash

        salt '*' user.info root
    '''
    user = _find_user('/Search', name)
    if user is None:
        return None

    attrs, err = user.recordDetailsForAttributes_error_(None, None)
    if err is not None:
        log.error('failed to retrieve attributes for user {}, reason: {}'.format(name, err.localizedDescription()))

    return _format_info(attrs)


def primary_group(name):
    '''
    Return the primary group of the named user

    .. versionadded:: 2016.3.0

    CLI Example:

    .. code-block:: bash

        salt '*' user.primary_group saltadmin
    '''
    user = info(name)
    if user is None:
        return None

    return user.get(kODAttributeTypePrimaryGroupID)

# def list_groups(name):
#     '''
#     Return a list of groups the named user belongs to.
#
#     name
#
#         The name of the user for which to list groups. Starting in Salt Carbon,
#         all groups for the user, including groups beginning with an underscore
#         will be listed.
#
#         .. versionchanged:: Carbon
#
#     CLI Example:
#
#     .. code-block:: bash
#
#         salt '*' user.list_groups foo
#     '''


def list_users():
    '''
    Return a list of all users

    CLI Example:

    .. code-block:: bash

        salt '*' user.list_users
    '''
    users = getent()
    if users is None:
        return None

    # NOTE: did not use a list comprehension because each user record can actually have multiple usernames
    # this means that the system can resolve two distinct usernames as one account.
    usernames = []
    for user in users:
        names = user[kODAttributeTypeRecordName]
        for name in names:
            usernames.append(name)

    return usernames


def rename(name, new_name):
    '''
    Change the username for a named user

    CLI Example:

    .. code-block:: bash

        salt '*' user.rename name new_name
    '''
    return _update_attribute(name, kODAttributeTypeRecordName, new_name)


def _update_attribute(name, od_attribute, value, commit=True):
    '''
    Update an Open Directory attribute for the given user name.
    :param name: username
    :param od_attribute: attribute type (usually from kODAttributeType*)
    :param value: The new value
    :return: boolean value indicating whether the record was updated.
    '''
    user = _find_user('/Local/Default', name)
    if user is None:
        raise CommandExecutionError(
            'user {} does not exist'.format(name)
        )

    didSet, err = user.setValue_forAttribute_error_(value, od_attribute, None)
    if err is not None:
        log.error('failed to set attribute {} on user {}, reason: {}'.format(od_attribute, name, err.localizedDescription()))

    synced, err = user.synchronizeAndReturnError_(None)
    if err is not None:
        raise CommandExecutionError(
            'could not save updated user record, reason: {}'.format(err.localizedDescription())
        )

    if not synced:
        return False

    return True


def _get_node(path):
    '''
    Get a reference to an ODNode instance given a path string eg. /LDAPv3/127.0.0.1
    '''
    session = ODSession.defaultSession()
    node, err = ODNode.nodeWithSession_name_error_(session, path, None)

    if err:
        raise CommandExecutionError(
            'cannot retrieve ODNode instance for path: {}, reason: {}'.format(path, err.localizedDescription())
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

