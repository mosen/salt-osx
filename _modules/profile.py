# -*- coding: utf-8 -*-
'''
Profiles Module
===============

Manage locally installed configuration profiles (.mobileconfig)

:maintainer:    Mosen <mosen@github.com>
:maturity:      new
:depends:       objc
:platform:      darwin
'''

import logging
import salt.utils
import salt.exceptions
import tempfile
import os
import plistlib
import uuid
import hashlib
import re
import binascii

log = logging.getLogger(__name__)

__virtualname__ = 'profile'


def __virtual__():
    return __virtualname__ if salt.utils.is_darwin() else False


def _content_to_uuid(payload):
    '''
    Generate a UUID based upon the payload content

    :param payload:
    :return:
    '''
    str_payload = plistlib.writePlistToString(payload)
    hashobj = hashlib.md5(str_payload)
    pattern = r'/\A([0-9a-f]{8})([0-9a-f]{4})([0-9a-f]{4})([0-9a-f]{4})([0-9a-f]{12})\z/'
    identifier = re.sub(pattern, r'\\1-\\2-\\3-\\4-\\5', binascii.hexlify(hashobj.digest()))

    return identifier


def _add_activedirectory_keys(payload):
    '''
    As per dayglojesus/managedmac, an excerpt from mobileconfig.rb:199

    The Advanced Active Directory profile contains flag keys which inform
    the installation process which configuration keys should actually be
    activated.

    http://support.apple.com/kb/HT5981?viewlocale=en_US&locale=en_US

    For example, if we wanted to change the default shell for AD accounts, we
    would actually need to define two keys: a configuration key and a flag key.

    <key>ADDefaultUserShell</key>
    <string>/bin/zsh</string>

    <key>ADDefaultUserShellFlag</key>
    <true/>

    If you fail to specify this second key (the activation or "flag" key), the
    configuration key will be ignored when the mobileconfig is processed.

    To avoid having to activate and deactivate the configuration keys, we
    pre-process the content array by overriding the transform_content method
    and shoehorn these flag keys into place dynamically, as required.
    :param payload:
    :return:
    '''
    needs_flag = ['ADAllowMultiDomainAuth',
                  'ADCreateMobileAccountAtLogin',
                  'ADDefaultUserShell',
                  'ADDomainAdminGroupList',
                  'ADForceHomeLocal',
                  'ADNamespace',
                  'ADPacketEncrypt',
                  'ADPacketSign',
                  'ADPreferredDCServer',
                  'ADRestrictDDNS',
                  'ADTrustChangePassIntervalDays',
                  'ADUseWindowsUNCPath',
                  'ADWarnUserBeforeCreatingMA']

    for k in payload.keys():
        if k in needs_flag:
            payload[needs_flag[k]] = True


def _transform_content(content, identifier):
    '''
    As dayglojesus/managedmac notes:
    PayloadUUID for each Payload is modified MD5sum of the payload itself, minus some keys.
    We can use this to check whether or not the content has been modified. Even when the attributes cannot
    be compared (as with passwords, which are omitted).

    :param content:
    :return:
    '''
    if not content:
        return list()

    transformed = list()

    for payload in content:
        for payload_type, data in payload.items():
            trans = dict()

            trans['PayloadType'] = payload_type

            if 'PayloadUUID' in trans:
                del trans['PayloadUUID']

            embedded_payload_uuid = _content_to_uuid(data)

            if 'PayloadIdentifier' in trans:
                embedded_payload_id = trans['PayloadIdentifier']
            else:
                embedded_payload_id = "{}.{}".format(identifier, embedded_payload_uuid)

            trans['PayloadIdentifier'] = embedded_payload_id
            trans['PayloadUUID'] = embedded_payload_uuid
            trans['PayloadEnabled'] = True
            trans['PayloadVersion'] = 1

            # if trans['PayloadType'] == 'com.apple.DirectoryService.managed':
            #     _add_activedirectory_keys(data)

            trans['PayloadContent'] = data

            trans['PayloadDescription'] = 'Payload level description'
            trans['PayloadDisplayName'] = 'Payload level displayname'
            trans['PayloadOrganization'] = 'Payload level org'
            transformed.append(trans)

    return transformed




def items():
    '''
    Retrieve all profiles in full

    CLI Example:

    .. code-block:: bash

        salt '*' profiles.items
    '''
    tmpdir = tempfile.mkdtemp('.profiles')
    tmpfile = os.path.join(tmpdir, 'profiles.plist')

    status = __salt__['cmd.retcode']('/usr/bin/profiles -P -o {}'.format(tmpfile))

    if not status == 0:
        raise salt.exceptions.CommandExecutionError(
            'Failed to read profiles or write to temporary file'
        )

    profiles = plistlib.readPlist(tmpfile)
    os.unlink(tmpfile)
    os.rmdir(tmpdir)

    return profiles


def installed(identifier):
    '''
    Determine whether a profile with the given identifier is installed.
    Returns True or False

    CLI Example:

    .. code-block:: bash

        salt '*' profiles.installed com.apple.mdm.hostname.local.ABCDEF
    '''
    profiles = __salt__['profile.items']()

    for domain, payload_content in profiles.items():
        for payload in payload_content:
            if payload['ProfileIdentifier'] == identifier:
                return True

    return False


def generate(identifier, description, displayname, organization, content, removaldisallowed=False, **kwargs):
    '''
    Generate a configuration profile.

    Intended to be used by other execution and state modules to prepare a profile for installation.
    Not really intended for CLI usage.

    identifier
        The profile identifier, which is the primary key for identifying whether a profile is installed.

    description
        Description of the profile

    displayname
        The name of the profile shown to the user

    organization
        The organization issuing the profile

    content
        The payload content for the profile, as a hash

    removaldisallowed : False
        Whether removal of the profile will be allowed
    '''
    profile_uuid = uuid.uuid4()
    log.debug("Creating new profile with UUID: {}".format(str(profile_uuid)))

    # As per managedmac for puppet, it's necessary to generate UUIDs for each payload based upon the content
    # in order to detect changes to the payload.
    # Transform a dict of { type: data } to { PayloadContent: data, }
    transformed = _transform_content(content, identifier)

    document = {
        'PayloadIdentifier': identifier,
        'PayloadDescription': description,
        'PayloadDisplayName': displayname,
        'PayloadOrganization': organization,
        'PayloadRemovalDisallowed': (removaldisallowed == True),
        'PayloadScope': 'System',
        'PayloadType': 'Configuration',
        'PayloadUUID': str(profile_uuid),
        'PayloadVersion': 1,
        'PayloadContent': transformed
    }

    plist_content = plistlib.writePlistToString(document)
    return plist_content


def install(path):
    '''
    Install a configuration profile.

    path
        Full path to the configuration profile to install
    '''
    status = __salt__['cmd.retcode']('/usr/bin/profiles -I -F {}'.format(path))

    if not status == 0:
        raise salt.exceptions.CommandExecutionError(
            'Failed to install profile at path: {}'.format(path)
        )

    return True


def remove(identifier):
    '''
    Remove a configuration profile by its profile identifier

    identifier
        The ProfileIdentifier
    '''
    status = __salt__['cmd.retcode']('/usr/bin/profiles -R -p {}'.format(identifier))

    if not status == 0:
        raise salt.exceptions.CommandExecutionError(
            'Failed to remove profile with identifier: {}'.format(path)
        )

    return True