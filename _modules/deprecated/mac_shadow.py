# -*- coding: utf-8 -*-
'''
Manage Mac OSX local directory passwords and policies.

Note that it is usually better to apply password policies through the creation of a configuration profile.

Tech Notes:
Usually when a password is changed by the system, there's a responsibility to check the hash list and generate hashes
for each. Many osx password changing scripts/modules only deal with the SHA-512 PBKDF2 hash when working with the local
node.
'''
# Authentication concepts reference:
# https://developer.apple.com/library/mac/documentation/Networking/Conceptual/Open_Directory/openDirectoryConcepts/openDirectoryConcepts.html#//apple_ref/doc/uid/TP40000917-CH3-CIFCAIBB

from __future__ import absolute_import

import logging

log = logging.getLogger(__name__)  # Start logging

import os
import base64
import salt.utils
import string
import binascii
import salt.exceptions

try:
    from passlib.utils import pbkdf2, ab64_encode, ab64_decode
    HAS_PASSLIB = True
except ImportError:
    HAS_PASSLIB = False


def __virtual__():
    if HAS_PASSLIB and salt.utils.platform.is_darwin():
        return True
    else:
        return False


def _pl_salted_sha512_pbkdf2_from_string(strvalue, salt_bin=None, iterations=1000):
    '''
    Create a PBKDF2-SHA512 hash with a 128 byte key length.
    The standard passlib.hash.pbkdf2_sha512 functions assume a 64 byte key length which does not match OSX's
    implementation.

    :param strvalue: The string to derive the hash from
    :param salt: The (randomly generated) salt
    :param iterations: The number of iterations, for Mac OS X it's normally between 23000-25000? need to confirm.
    :return: (binary digest, binary salt, number of iterations used)
    '''
    if salt_bin is None:
        salt_bin = os.urandom(32)

    key_length = 128
    hmac_sha512, dsize = pbkdf2.get_prf("hmac-sha512")
    digest_bin = pbkdf2.pbkdf2(strvalue, salt_bin, iterations, key_length, hmac_sha512)

    return digest_bin, salt_bin, iterations


def _extract_authdata(item):
    '''
    Extract version, authority tag, and authority data from a single array item of AuthenticationAuthority

    item
        The NSString instance representing the authority string

    returns
        version (default 1.0.0), tag, data as a tuple
    '''
    parts = string.split(item, ';', 2)

    if not parts[0]:
        parts[0] = '1.0.0'

    return {
        'version': parts[0],
        'tag': parts[1],
        'data': parts[2]
    }


def authorities(name):
    '''
    Read the list of authentication authorities for the given user.

    name
        Short username of the local user.
    '''
    authorities_plist = __salt__['cmd.run']('/usr/bin/dscl -plist . read /Users/{0} AuthenticationAuthority'.format(name))
    plist = __salt__['plist.parse_string'](authorities_plist)
    authorities_list = [_extract_authdata(item) for item in plist.objectForKey_('dsAttrTypeStandard:AuthenticationAuthority')]

    return authorities_list


def user_shadowhash(name):
    '''
    Read the existing hash for the named user.
    Returns a dict with the ShadowHash content for the named user in the form:

    { 'HASH_TYPE': { 'entropy': <base64 hash>, 'salt': <base64 salt>, 'iterations': <n iterations> }}

    Hash types are hard coded to SALTED-SHA-PBKDF2, CRAM-MD5, NT, RECOVERABLE.
    In future releases the AuthenticationAuthority property should be checked for the hash list

    name
        The username associated with the local directory user.
    '''

    # We have to strip the output string, convert hex back to binary data, read that plist and get our specific
    # key/value property to find the hash. I.E there's a lot of unwrapping to do.
    log.debug('Reading ShadowHashData')
    data = __salt__['dscl.read']('.', '/Users/{0}'.format(name), 'ShadowHashData')
    log.debug('Got ShadowHashData')
    log.debug(data)

    if data is None:
        log.debug('No such record/attribute found, returning None')
        return None

    if 'dsAttrTypeNative:ShadowHashData' not in data:
        raise salt.exceptions.SaltInvocationError(
            'Expected to find ShadowHashData in user record: {0}'.format(name)
        )


    plist_hex = string.replace(data['dsAttrTypeNative:ShadowHashData'], ' ', '')
    plist_bin = binascii.unhexlify(plist_hex)

    # plistlib is not used, because mavericks ships without binary plist support from plistlib.
    plist = __salt__['plist.parse_string'](plist_bin)

    log.debug(plist)

    pbkdf = plist.objectForKey_('SALTED-SHA512-PBKDF2')
    cram_md5 = plist.objectForKey_('CRAM-MD5')
    nt = plist.objectForKey_('NT')
    recoverable = plist.objectForKey_('RECOVERABLE')

    hashes = {}

    if pbkdf is not None:
        hashes['SALTED-SHA512-PBKDF2'] = {
            'entropy': pbkdf.objectForKey_('entropy').base64EncodedStringWithOptions_(0),
            'salt': pbkdf.objectForKey_('salt').base64EncodedStringWithOptions_(0),
            'iterations': pbkdf.objectForKey_('iterations')
        }

    if cram_md5 is not None:
        hashes['CRAM-MD5'] = cram_md5.base64EncodedStringWithOptions_(0)

    if nt is not None:
        hashes['NT'] = nt.base64EncodedStringWithOptions_(0)

    if recoverable is not None:
        hashes['RECOVERABLE'] = recoverable.base64EncodedStringWithOptions_(0)

    return hashes


def info(name):
    '''
    Return information for the specified user

    CLI Example:

    .. code-block:: bash

        salt '*' mac_shadow.info admin
    '''
    # dscl -plist . -read /Users/<User> ShadowHashData
    # Read out name from dscl
    # Read out passwd hash from decrypted ShadowHashData in dslocal
    # Read out lstchg/min/max/warn/inact/expire from PasswordPolicy
    pass


def gen_password(password, salt=None, iterations=None):
    '''
    Generate hashed (PBKDF2-SHA512) password
    Returns a dict containing values for 'entropy', 'salt' and 'iterations'.

    password
        Plaintext password to be hashed.

    salt
        Cryptographic salt (base64 encoded). If not given, a random 32-character salt will be
        generated. (32 bytes is the standard salt length for OSX)

    iterations
        Number of iterations for the key derivation function, default is 1000

    CLI Example:

    .. code-block:: bash

        salt '*' mac_shadow.gen_password 'I_am_password'
        salt '*' mac_shadow.gen_password 'I_am_password' 'Ausrbk5COuB9V4ata6muoj+HPjA92pefPfbW9QPnv9M=' 23000
    '''
    if iterations is None:
        iterations = 1000

    if salt is None:
        salt_bin = os.urandom(32)
    else:
        salt_bin = base64.b64decode(salt, '+/')

    entropy, used_salt, used_iterations = _pl_salted_sha512_pbkdf2_from_string(password, salt_bin, iterations)

    result = {
        'entropy': base64.b64encode(entropy, '+/'),
        'salt': base64.b64encode(used_salt, '+/'),
        'iterations': used_iterations
    }

    return {'SALTED-SHA512-PBKDF2': result}


def set_password_hash(name, hashtype, hash, salt=None, iterations=None):
    '''
    Set the given hash as the shadow hash data for the named user.

    name
        The name of the local user, which is assumed to be in the local directory service.

    hashtype
        A valid hash type, one of: PBKDF2, CRAM-MD5, NT, RECOVERABLE

    hash
        The computed hash

    salt (optional)
        The salt to use, if applicable.

    iterations
        The number of iterations to use, if applicable.
    '''
    # current_hashes = user_shadowhash(name)
    # current_pbkdf2 = current_hashes['SALTED-SHA512-PBKDF2']
    #
    # log.debug('Current ShadowHashdata follows')
    # log.debug(current_hashes)

    shd = {'SALTED-SHA512-PBKDF2': {'entropy': hash, 'salt': salt, 'iterations': iterations}}
    log.debug('Encoding following dict as bplist')
    log.debug(shd)

    # if shd['SALTED-SHA512-PBKDF2']['entropy'] == current_pbkdf2['entropy']:
    #     log.debug('Entropy IS EQUAL!')

    shd_bplist = __salt__['plist.gen_string'](shd, 'binary')
    shd_bplist_b64 = base64.b64encode(shd_bplist, '+/')

    log.debug('Flushing directory services cache')
    __salt__['dscl.flushcache']()

    log.debug('Writing directly to dslocal')
    __salt__['plist.append_key']('/var/db/dslocal/nodes/Default/users/{0}.plist'.format(name),
                                 'ShadowHashData',
                                 'data',
                                 shd_bplist_b64)

    log.debug('Flushing directory services cache')
    __salt__['dscl.flushcache']()

    return True

def set_password(name, password, salt=None, iterations=None):
    '''
    Set the password for a named user (insecure).
    Use mac_shadow.set_password_hash to supply pre-computed hash values.

    For the moment this sets only the PBKDF2-SHA512 salted hash.
    To be a good citizen we should set every hash in the authority list.

    name
        The name of the local user, which is assumed to be in the local directory service.

    password
        The plaintext password to set (warning: insecure, used for testing)

    salt
        The salt to use, defaults to automatically generated.

    iterations
        The number of iterations to use, defaults to an automatically generated random number.

    CLI Example:

    .. code-block:: bash

        salt '*' mac_shadow.set_password macuser macpassword
    '''
    #current_hashes = user_shadowhash(name)
    #current_pbkdf2 = current_hashes['SALTED-SHA512-PBKDF2']
    # hash = gen_password(password, current_pbkdf2['salt'], current_pbkdf2['iterations'])
    hash = gen_password(password, salt, iterations)
    #
    # log.debug('Current ShadowHashData follows')
    # if current_hashes:
    #     log.debug(current_hashes)
    #
    #     if hash['SALTED-SHA512-PBKDF2']['entropy'] == current_pbkdf2['entropy']:
    #         return False  # No change required
    # else:
    #     log.debug('No Shadow Hash Data exists for User: {0}'.format(name))

    set_password_hash(
        name,
        'PBKDF2',
        hash['SALTED-SHA512-PBKDF2']['entropy'],
        hash['SALTED-SHA512-PBKDF2']['salt'],
        hash['SALTED-SHA512-PBKDF2']['iterations']
    )

    return True

def del_password(name):
    '''
    Delete the password from name user

    CLI Example:

    .. code-block:: bash

        salt '*' shadow.del_password username
    '''
    pass  # Re-order authentication authority and remove ShadowHashData
