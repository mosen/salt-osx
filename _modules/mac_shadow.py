# -*- coding: utf-8 -*-
'''
Manage Mac OSX local directory passwords and policies.

Note that it is usually better to apply password policies through the creation of a configuration profile.

Tech Notes:
Usually when a password is changed by the system, there's a responsibility to check the hash list and generate hashes
for each. Many osx password changing scripts/modules only deal with the SHA-512 PBKDF2 hash when working with the local
node.
'''
from __future__ import absolute_import

import os
import base64
import salt.utils
import string
import binascii
import tempfile

try:
    from passlib.utils import pbkdf2, ab64_encode, ab64_decode
    HAS_PASSLIB = True
except ImportError:
    HAS_PASSLIB = False


def __virtual__():
    if HAS_PASSLIB and salt.utils.is_darwin():
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

def read_shadowhash(name):
    '''
    Read the existing hash for the named user.

    name
        The username associated with the local directory user.
    '''
    # Note: I've tried as best I could to keep third party dependencies out of this module.
    # You could just as easily use PyObjC or plistlib, but I felt that portability was important.
    tmpdir = tempfile.mkdtemp('.shadowhash')
    tmpfile = os.path.join(tmpdir, 'shadowhash.plist')

    # We have to strip the output string, convert hex back to binary data, read that plist and get our specific
    # key/value property to find the hash. I.E there's a lot of unwrapping to do.
    data = __salt__['cmd.run']('/usr/bin/dscl . read /Users/{0} ShadowHashData'.format(name))
    parts = string.split(data, '\n')
    plist_hex = string.replace(parts[1], ' ', '')
    f = file(tmpfile, 'w')
    f.write(binascii.unhexlify(plist_hex))
    f.close()
    return tmpfile



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


def gen_password(password, salt=None, iterations=1000):
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

    return result


def set_password(name, password, salt=None, iterations=None):
    '''
    Set the password for a named user. In Mac OSX 10.8 and later, the password hash,
    its salt, and the number of iterations must be specified. To generate these from plain text
    you may use the mac_shadow.gen_password execution module.

    CLI Example:

    .. code-block:: bash

        salt '*' mac_shadow.set_password macuser 'PBKDF2-SHA512 hash (128 bytes)' 'Ausrbk5COuB9V4ata6muoj+HPjA92pefPfbW9QPnv9M=' 23000
    '''
    pass


def del_password(name):
    '''
    Delete the password from name user

    CLI Example:

    .. code-block:: bash

        salt '*' shadow.del_password username
    '''
    pass