"""
Query and modify user and system keychains

Straight adaptation from pudquick's keymaster.py

:maintainer:    Mosen <mosen@github.com>
:maturity:      new
:depends:       objc,ctypes,CoreFoundation
:platform:      darwin
"""

import logging
import salt.exceptions

log = logging.getLogger(__name__)

HAS_LIBS = False
try:
    import os.path, base64
    from ctypes import CDLL, Structure, POINTER, byref, addressof, create_string_buffer, c_int, c_uint, c_ubyte, \
        c_void_p, c_size_t
    from CoreFoundation import kCFStringEncodingUTF8

    Security = CDLL('/System/Library/Frameworks/Security.Framework/Versions/Current/Security')
    # I don't use the pyObjC CoreFoundation import because it attempts to bridge between CF, NS, and python.
    # When you try to mix it with Security.Foundation (pure C / CF), you get nasty results.
    # So I directly import CoreFoundation to work with CFTypes to keep it pure of NS/python bridges.
    CFoundation = CDLL('/System/Library/Frameworks/CoreFoundation.Framework/Versions/Current/CoreFoundation')

    HAS_LIBS = True
except ImportError:
    pass

__virtualname__ = 'keychain'


def __virtual__():
    '''
    Only load if the platform is correct and we can use PyObjC libs
    '''
    if __grains__.get('kernel') != 'Darwin':
        return False

    if not HAS_LIBS:
        return False

    return __virtualname__


def _secErrorMessage(errCode):
    '''
    Retrieve a useful error message, given a return code from the Security framework
    :param errCode:
    :return: string
    '''
    if errCode == -25291:
        return "No trust results are available."
    elif errCode == -25292:
        return "Read only error."
    elif errCode == -25293:
        return "Authorization/Authentication failed."
    elif errCode == -25294:
        return "The keychain does not exist."
    elif errCode == -25295:
        return "The keychain is not valid."
    elif errCode == -25296:
        return "A keychain with the same name already exists."
    elif errCode == -25297:
        return "More than one callback of the same name exists."
    elif errCode == -25298:
        return "The callback is not valid."
    elif errCode == -25299:
        return "The item already exists."
    elif errCode == -25300:
        return "The item cannot be found."
    elif errCode == -25301:
        return "The buffer is too small."
    elif errCode == -25302:
        return "The data is too large."
    elif errCode == -25303:
        return "The attribute does not exist."
    elif errCode == -25304:
        return "The item reference is invalid."
    elif errCode == -25305:
        return "The search reference is invalid."
    elif errCode == -25306:
        return "The keychain item class does not exist."
    elif errCode == -25307:
        return "A default keychain does not exist."
    elif errCode == -25308:
        return "Interaction is not allowed with the Security Server."
    elif errCode == -25309:
        return "The attribute is read only."
    elif errCode == -25310:
        return "The version is incorrect."
    elif errCode == -25311:
        return "The key size is not allowed."
    elif errCode == -25312:
        return "There is no storage module available."
    elif errCode == -25313:
        return "There is no certificate module available."
    elif errCode == -25314:
        return "There is no policy module available."
    elif errCode == -25315:
        return "User interaction is required."
    elif errCode == -25316:
        return "The data is not available."
    elif errCode == -25317:
        return "The data is not modifiable."
    elif errCode == -25318:
        return "The attempt to create a certificate chain failed."

    elif errCode == -25240:
        return "The access control list is not in standard simple form."
    elif errCode == -25241:
        return "The policy specified cannot be found."
    elif errCode == -25242:
        return "The trust setting is invalid."
    elif errCode == -25243:
        return "The specified item has no access control."
    elif errCode == -25244:
        return "errSecInvalidOwnerEdit (No description available)"
    else:
        return "No description available for error: {}".format(errCode)


class OpaqueType(Structure):
    pass

# Combined with the above, this is essentially an opaque wrapper around pointers to various
# data types. Just enough syntactic sugar to keep python from bugging out with raw C pointers.
OpaqueTypeRef = POINTER(OpaqueType)

# Per <sys/param.h> and <sys/syslimits.h>
MAXPATHLEN = 1024

# Setting the return type to one of our opaque pointer wrappers so python doesn't bug out.
CFArrayCreate = CFoundation.CFArrayCreate
CFArrayCreate.restype = OpaqueTypeRef
CFArrayCreateMutable = CFoundation.CFArrayCreateMutable
CFArrayCreateMutable.restype = OpaqueTypeRef
CFArrayGetValueAtIndex = CFoundation.CFArrayGetValueAtIndex
CFArrayGetValueAtIndex.restype = OpaqueTypeRef
CFDataCreate = CFoundation.CFDataCreate
CFDataCreate.restype = OpaqueTypeRef
CFStringCreateWithCString = CFoundation.CFStringCreateWithCString
CFStringCreateWithCString.restype = OpaqueTypeRef

CSSM_CERT_X_509v3 = 3
CSSM_CERT_ENCODING_DER = 3

kSecFormatUnknown = 0
kSecItemTypeUnknown = 0
kSecKeySecurePassphrase = 2

kSecTrustSettingsDomainUser = 0
kSecTrustSettingsDomainAdmin = 1
kSecTrustSettingsDomainSystem = 2  # System trust settings are read-only, even by root

# Per SecKeychain.h
kSecPreferencesDomainUser = 0
kSecPreferencesDomainSystem = 1
# kSecPreferencesDomainCommon    = 2
# Interestingly, https://developer.apple.com/library/mac/documentation/security/Reference/keychainservices/Reference/reference.html
# also includes kSecPreferencesDomainAlternate and kSecPreferencesDomainDynamic.
# However, kSecPreferencesDomainAlternate is not listed in SecKeychain.h, which means the header file disagrees with the
# documentation on the enumeration value for the domains. In testing with SecKeychainCopyDomainSearchList, it doesn't recognize a
# value beyond 3 - so that would seem to indicate the public documentation is wrong. Doesn't really matter since we don't
# care about these two anyways - just something odd to note.

class SecKeychainSettings(Structure):
    pass


SecKeychainSettings._fields_ = [
    ('version', c_uint),
    ('lockOnSleep', c_ubyte),
    ('useLockInterval', c_ubyte),
    ('lockInterval', c_uint),
]


class SecKeyImportExportParameters(Structure):
    pass


SecKeyImportExportParameters._fields_ = [
    ('version', c_uint),
    ('flags', c_uint),
    ('passphrase', OpaqueTypeRef),
    ('alertTitle', OpaqueTypeRef),
    ('alertPrompt', OpaqueTypeRef),
    ('accessRef', OpaqueTypeRef),
    ('keyUsage', c_uint),
    ('keyAttributes', c_uint),
]


class CSSM_DATA(Structure):
    pass


CSSM_DATA._fields_ = [
    ('Length', c_size_t),
    ('Data', c_void_p),
]


def _safe_release(cf_ref):
    """Release a CFReference safely (if there is one)"""
    if cf_ref:
        CFoundation.CFRelease(cf_ref)


def _get_keychain_path(a_keychain):
    """Copy the path of a keychain into a string buffer"""
    path_length = c_int(MAXPATHLEN)
    path_name = create_string_buffer('\0' * (MAXPATHLEN + 1), MAXPATHLEN + 1)
    result = Security.SecKeychainGetPath(a_keychain, byref(path_length), path_name)
    # We don't even need the path_length because path_name was made with the create_string_buffer
    # helper, which has nice python bindings around C strings / auto detection for null termination
    return path_name.value


def _resolve_keychain_name(keychain_name):
    """Get a keychains full path given only its short name"""
    keychainRef = OpaqueTypeRef()
    result = Security.SecKeychainOpen(keychain_name, byref(keychainRef))
    if not keychainRef:
        # Weird, it couldn't resolve - this shouldn't happen
        return None
    # Get the path
    keychain_path = _get_keychain_path(keychainRef)
    # Release the ref
    _safe_release(keychainRef)
    return keychain_path


def set_settings(keychain, sleep_lock=False, interval_lock=False, interval_time=2147483647):
    '''
    Set keychain settings

    keychain
        The keychain, which may be a short name or the full path to the keychain

    sleep_lock
        True or false indicating whether the keychain should be locked on sleep or not

    interval_lock
        True or false indicating whether the keychain should be locked after some interval or not

    interval_time
        The number of seconds before the keychain will be locked automatically, if interval_lock is True.
        If you set this to anything other than the default, it implies that interval_lock is True.

    CLI Example:

    .. code-block:: bash

        salt '*' keychain.set_settings keychain False True 120
    '''
    # If you unlock the keychain before changing settings, you do not get prompted via GUI for non-root
    # Setting the interval time to anything other than the default 2147483647 overrides/ignores any value
    # for interval_lock and forces it to True.

    status = __salt__['keychain.status'](keychain)
    if not status['usable']:
        raise salt.exceptions.CommandExecutionError('Error: No such keychain')

    # Make our settings object
    # Version number for settings is supposed to be '1'
    settings_struct = SecKeychainSettings(1, sleep_lock, interval_lock, interval_time)
    if settings_struct.lockInterval != 2147483647:
        interval_lock = True

    keychainRef = OpaqueTypeRef()
    result = Security.SecKeychainOpen(keychain, byref(keychainRef))
    if not keychainRef:
        raise salt.exceptions.CommandExecutionError(
            "Error: Could not modify settings for keychain, because we couldnt get a reference to it."
        )

    result = Security.SecKeychainSetSettings(keychainRef, byref(settings_struct))
    _safe_release(keychainRef)

    if result != 0:
        return False
    else:
        return True


def get_settings(keychain):
    '''
    Get keychain settings.
    Will return a hash {'sleep_lock': False, 'interval_lock'=False, 'interval_time'=nnn}

    keychain
        The keychain, which may be the file name only for the user "login.keychain" or the full path to the keychain for
        both user and system keychains.
    '''
    # If you unlock the keychain before changing settings, you do not get prompted via GUI for non-root
    # Results returned are: bool sleep_lock, bool interval_lock, int interval_time (in seconds)
    status = __salt__['keychain.status'](keychain)

    if not status['usable']:
        raise salt.exceptions.CommandExecutionError('Error: No such keychain')

    settings_struct = SecKeychainSettings(1, 0, 0, 0)

    keychainRef = OpaqueTypeRef()
    result = Security.SecKeychainOpen(keychain, byref(keychainRef))
    if not keychainRef:
        raise salt.exceptions.CommandExecutionError(
            "Error: Could not modify settings for keychain, because we couldnt get a reference to it."
        )

    result = Security.SecKeychainCopySettings(keychainRef, byref(settings_struct))
    _safe_release(keychainRef)

    if result != 0:
        raise salt.exceptions.CommandExecutionError(
            'Error: Something went wrong with that settings change', result
        )
    else:
        # Apparently useLockInterval is always false. Whether it will lock or not is purely based on the timer value.
        return {
            'sleep_lock': bool(settings_struct.lockOnSleep),
            'interval_lock': settings_struct.lockInterval != 2147483647,
            'interval_time': settings_struct.lockInterval
        }


def _keychain_import_cert(keychain_name, cert_path):
    # WARNING - ROUGH CODE, NO ERROR HANDLING YET
    # No trust model here, good for client certs - not for CAs
    # Yay, it works! - Still need to add error checking and result checking
    #
    # Read in the cert_path first
    cert_handle = open(cert_path, 'rb')
    cert_data = cert_handle.read()
    cert_handle.close()
    # Create a CFData reference with it
    inData = CFDataCreate(None, cert_data, len(cert_data))
    # Get the keychain ref
    keychainRef = OpaqueTypeRef()
    result = Security.SecKeychainOpen(keychain_name, byref(keychainRef))
    keyParams = SecKeyImportExportParameters(0, 0, None, None, None, None, 0, 0)
    keyParams.flags = kSecKeySecurePassphrase
    fileStr = CFStringCreateWithCString(None, os.path.split(os.path.abspath(cert_path))[-1], kCFStringEncodingUTF8)
    dummyStr = CFStringCreateWithCString(None, "You should never see this, something went wrong.",
                                         kCFStringEncodingUTF8)
    keyParams.alertPrompt = dummyStr
    outArray = OpaqueTypeRef()
    result = Security.SecKeychainItemImport(inData, fileStr, None, None, 0, byref(keyParams), keychainRef,
                                            byref(outArray))
    # Cleanup
    _safe_release(outArray)
    _safe_release(fileStr)
    _safe_release(dummyStr)
    _safe_release(keychainRef)
    _safe_release(inData)
    if result != 0:
        raise Exception('Error: Error importing certificate into keychain', result)


def add_trusted_cert(keychain, cert_path):
    '''
    Add a trusted certificate (PEM format) to a keychain.
    Returns true if certificate was imported and trusted.

    NOTE: If operating on a users keychain, the user will get a dialog asking for a password to change their
    keychain settings.

    keychain
        The full path to the keychain. Filename may be used if modifying a keychain for the current user.

    cert_path
        The path to the certificate to add as trusted
    '''
    # When used as a user in graphical mode - will cause a GUI prompt
    # When used as root, for one of root's keychains - does not cause a GUI prompt
    # TODO: Add some checks to make sure that unwanted GUI prompts do not appear
    domain = kSecTrustSettingsDomainUser
    trustSettings = None

    keychainRef = OpaqueTypeRef()
    result = Security.SecKeychainOpen(keychain, byref(keychainRef))

    if not keychainRef:
        raise salt.exceptions.CommandExecutionError(
            "Could not get a reference to the specified keychain. \
            This should never happen. code: {0}, message: {1} ".format(result, _secErrorMessage(result))
        )

    cert_handle = open(cert_path, 'rb')
    cert_data = cert_handle.read()
    cert_handle.close()
    if not (('-----BEGIN ' in cert_data) and ('-----END ' in cert_data)):
        raise salt.exceptions.CommandExecutionError('Error: Certificate does not appear to be .pem file')

    # Decode the base64 data
    core_data = \
    cert_data.split('-----BEGIN ', 1)[-1].replace('\r', '\n').split('-----\n', 1)[-1].split('\n-----END ', 1)[0]
    core_data = ''.join(core_data.split('\n'))
    pem_data = create_string_buffer(base64.b64decode(core_data), len(core_data))

    # Create the CSSM_DATA struct, the API does not verify whether the certificate data is actually valid
    certData = CSSM_DATA(len(pem_data), addressof(pem_data))
    certRef = OpaqueTypeRef()
    result = Security.SecCertificateCreateFromData(byref(certData), CSSM_CERT_X_509v3, CSSM_CERT_ENCODING_DER,
                                                   byref(certRef))

    if result != 0:
        raise salt.exceptions.CommandExecutionError(
            "Failed to create certificate using the supplied data. \
            code: {0}, message: {1} ".format(result, _secErrorMessage(result))
        )

    result = Security.SecCertificateAddToKeychain(certRef, keychainRef)
    if result != 0:
        raise salt.exceptions.CommandExecutionError(
            "Failed to add certificate to keychain. \
            code: {0}, message: {1} ".format(result, _secErrorMessage(result))
        )

    result = Security.SecTrustSettingsSetTrustSettings(certRef, domain, trustSettings)
    if result != 0:
        raise salt.exceptions.CommandExecutionError(
            "Failed to set trust settings for the certificate. \
            code: {0}, message: {1} ".format(result, _secErrorMessage(result))
        )

    _safe_release(certRef)
    _safe_release(keychainRef)

    return True


def lock(path):
    '''
    Lock a keychain.

    path
        The full path to the keychain to lock
    '''
    status = __salt__['keychain.status'](path)

    if not status['usable']:
        raise Exception('Error: No such keychain')
    if not status['unlocked']:
        return True  # Already locked

    keychainRef = OpaqueTypeRef()
    result = Security.SecKeychainOpen(path, byref(keychainRef))

    if not keychainRef:
        raise salt.exceptions.CommandExecutionError(
            "Could not get a reference to the specified keychain. This should never happen. result: ", result
        )

    result = Security.SecKeychainLock(keychainRef)
    _safe_release(keychainRef)

    if result != 0:
        log.error('Error: Trying to lock keychain returned a non-zero status ', result)
        return False
    else:
        return True


def unlock(path, password):
    '''
    Unlock a keychain.

    path
        The full path to the keychain to unlock

    password
        The password required to unlock the keychain
    '''
    # As per pudquicks source: no UTF-8 yet
    status = __salt__['keychain.available'](path)

    if not status['usable']:
        raise Exception('Error: No such keychain')
    if status['unlocked']:
        # Already unlocked, no need to lock it again
        return True

    # Ok, time to unlock it
    keychainRef = OpaqueTypeRef()
    result = Security.SecKeychainOpen(path, byref(keychainRef))

    if not keychainRef:
        # Weird, it couldn't resolve - this shouldn't happen
        raise salt.exceptions.CommandExecutionError("Failed to open keychain for some unknown reason: ", result)
        # Perform unlock

    result = Security.SecKeychainUnlock(keychainRef, len(password), password, True)
    _safe_release(keychainRef)

    if result != 0:
        log.warning('Trying to unlock keychain failed, may be an incorrect password. result: ', result)
        return False
    else:
        return True


def keychains(domain='system'):
    '''
    Get a list of keychains

    domain
        The keychain domain referring to the 'system' or 'user' level keychain

    CLI Example:

    .. code-block:: bash

        salt '*' keychain.keychains [domain]
    '''
    if domain == 'user':
        kDomain = kSecPreferencesDomainUser
    elif domain == 'system':
        kDomain = kSecPreferencesDomainSystem
    else:
        raise salt.exceptions.CommandExecutionError('Unrecognised keychain domain given: {}'.format(domain))

    keychain_paths = []
    search_list = OpaqueTypeRef()
    log.debug('Looking up keychain search list from Security framework')

    # Look up our list of keychain paths in the user domain, pass the results back in search_list
    result = Security.SecKeychainCopyDomainSearchList(kDomain, byref(search_list))

    # Return code is zero on success
    if result != 0:
        log.error('Failed to get keychain search list, no reason given')
        raise salt.exceptions.CommandExecutionError(
            'Error: Could not get keychain search list for some reason'
        )

    # SecKeychainCopyDomainSearchList is pretty gross. It can return a single SecKeychainRef
    # ... OR it can return a CFArray of them. So you have to check what you're getting.

    if CFoundation.CFGetTypeID(search_list) == Security.SecKeychainGetTypeID():
        # It's a SecKeychain, just get the path value directly
        keychain_paths.append(_get_keychain_path(search_list))

    elif CFoundation.CFGetTypeID(search_list) == CFoundation.CFArrayGetTypeID():
        # It's a CFArray of SecKeychains, gotta loop
        count = CFoundation.CFArrayGetCount(search_list)
        for i in range(count):
            # Work with the items one at a time
            a_keychain = CFArrayGetValueAtIndex(search_list, i)
            keychain_paths.append(_get_keychain_path(a_keychain))
    return keychain_paths


def status(path):
    '''
    Check if keychain is available, and what its status is (usable, unlocked, readable, writable)

    path
        The fully qualified path to the keychain

    CLI Example:

    .. code-block:: bash

        salt '*' keychain.status /Library/Keychains/System.keychain
    '''
    # In the user domain
    # This is a higher level function the others rely on

    # Rewritten from pudquick's version to use dict, plays nicer with salt.
    #status = [False, None, None, None]
    status = {'usable': False, 'unlocked': None, 'readable': None, 'writable': None}

    keychainRef = OpaqueTypeRef()
    result = Security.SecKeychainOpen(path, byref(keychainRef))

    if not keychainRef:
        # Weird, it couldn't resolve - this shouldn't happen
        return status

    # Check on the status of the keychain
    status_mask = c_uint(0)
    result = Security.SecKeychainGetStatus(keychainRef, byref(status_mask))

    if result == 0:
        # Keychain is available and usable - now to unpack status_mask
        # Quick hack:
        # 1 = unlocked
        # 2 = readable
        # 4 = writable
        # Format the integer into a 3 digit binary string ('000','001', etc), map True for 1 & False for 0 per digit,
        # then reverse the order (so they're in order: 1, 2, 4)
        status_keys = ['unlocked', 'readable', 'writable']
        status_list = [True] + map(lambda x: x == '1', '{0:03b}'.format(status_mask.value))[::-1]
        status = dict(zip(status_keys, status_list))
        status['usable'] = True

    _safe_release(keychainRef)
    return status


def available(path):
    '''
    Check if keychain is available. Returns true or false

    path
        The fully qualified path to the keychain

    CLI Example:

    .. code-block:: bash

        salt '*' keychain.available /Library/Keychains/System.keychain
    '''
    return __salt__['keychain.status'](path)['usable']


def create(path, password, auto_search=True):
    '''
    Create a new keychain

    path
        The full path to the keychain to create

    password
        The keychain password

    auto_search [Optional]
        Whether the keychain should be immediately added to the search list.

    CLI Example:

    .. code-block:: bash

        salt '*' keychain.create <path> <password> [auto_search]
    '''

    if not password:
        raise salt.exceptions.CommandExecutionError('Error: Password must be provided')

    if __salt__['keychain.available'](path):
        raise salt.exceptions.CommandExecutionError('Error: Keychain already exists with this name')

    keychainRef = OpaqueTypeRef()

    # The zero is for 'do_prompt' for password
    # The None is for default access rights for the keychain
    result = Security.SecKeychainCreate(path, len(str(password)), str(password), 0, None, byref(keychainRef))
    _safe_release(keychainRef)

    if result != 0:
        raise Exception('Error: Could not create keychain', result)

    if auto_search:
        __salt__['keychain.add_search'](path)



def delete(path):
    '''
    Delete a keychain. This will refuse to remove login and system keychains.

    path
        The full path to the keychain to delete

    CLI Example:

    .. code-block:: bash

        salt '*' keychain.delete <path>
    '''
# def _delete_keychain(keychain_name):
    # For the time being here, dummy mode to keep from deleting login and System keychain
    full_name = _resolve_keychain_name(path)
    if full_name == _resolve_keychain_name('login.keychain'):
        log.warning('Refusing to delete login keychain')
        return False

    if full_name == '/Library/Keychains/System.keychain':
        log.warning('Refusing to delete system keychain')
        return False

    keychainRef = OpaqueTypeRef()
    # Always succeeds, safe to ignore result
    result = Security.SecKeychainOpen(path, byref(keychainRef))
    result = Security.SecKeychainDelete(keychainRef)
    _safe_release(keychainRef)

    if result != 0:
        raise salt.exceptions.CommandExecutionError('Error: Could not delete keychain', result)

    return True


def in_search(path):
    '''
    Determine whether a keychain is in the search path.
    Returns True or False

    path
        The full path of the keychain to check against the search list.

    CLI Example:

    .. code-block:: bash

        salt '*' keychain.in_search <path>
    '''
    keychains = __salt__['keychain.keychains']('user')
    return path in keychains

def add_search(path):
    '''
    Add a keychain to the search list.

    path
        The full path to the keychain to add

    CLI Example:

    .. code-block:: bash

        salt '*' keychain.add_search <path>
    '''
    # In the user domain
    if __salt__['keychain.in_search'](path):
        # It's already there, just return
        return

    # Otherwise, need to add it to the search path - it'll go at the end
    new_path_list = __salt__['keychain.keychains']()
    new_path_list.append(path)

    # Set our search path to the new list
    __salt__['keychain.set_search'](new_path_list)


def set_search(paths):
    '''
    Set the search list for keychains.

    paths
        keychains that should be in the search list.
    '''
    # def _set_keychain_search(keychain_list):
    # In the user domain
    # Note: SecKeychainOpen, by design, does not fail for keychain paths that don't exist.
    # Keychains can be kept on smartcard devices that fall under the 'dynamic' domain
    # in that they should be part of the search path, but aren't guaranteed to always be there.
    # See: http://lists.apple.com/archives/apple-cdsa/2006/Feb/msg00063.html
    # Also: Non-absolute paths are considered to be located (by SecKeychainOpen) in the
    # ~/Library/Keychains path. This isn't really well documented by Apple.
    problem = False
    if not paths:
        # Need to create a blank list and set our search path to it.
        search_arrayRef = CFArrayCreate(None, None, 0, CFoundation.kCFTypeArrayCallBacks)
    else:
        # One or more items. Need to create an array of them
        search_arrayRef = CFArrayCreateMutable(None, 0, CFoundation.kCFTypeArrayCallBacks)
        for keychain_path in paths:
            # Set up a null pointer to store the ref at
            keychainRef = OpaqueTypeRef()
            result = Security.SecKeychainOpen(keychain_path, byref(keychainRef))
            if (result != 0) or (not keychainRef):
                # There was a problem, don't set any paths
                problem = True
            else:
                # Append the keychain reference and release it
                result = CFoundation.CFArrayAppendValue(search_arrayRef, keychainRef)
                _safe_release(keychainRef)

    # Attempt to set the search paths
    result = Security.SecKeychainSetDomainSearchList(kSecPreferencesDomainUser, search_arrayRef)
    _safe_release(search_arrayRef)

    if (result != 0) or (problem):
        return False
    else:
        return True


def remove_search(path):
    '''
    Remove a keychain from the search list

    path
        The path to the keychain for removal
    '''
    # In the user domain, some safety to keep from removing a login keychain
    if not __salt__['keychain.in_search'](path):
        # It's not in the search path currently, so just return
        return False

    full_name = _resolve_keychain_name(path)
    if full_name == _resolve_keychain_name('login.keychain'):
        # Safety feature - don't want to remove the login keychain accidentally
        log.warning('Refusing to remove the login keychain')
        return False

    # Otherwise, it is in the search path - need to remove it
    new_path_list = __salt__['keychain.keychains']()
    # Remove it from the list
    new_path_list.remove(full_name)
    # Set our search path to the new list
    __salt__['keychain.set_search'](new_path_list)

    return True


def unlocked(path):
    '''
    Determine whether a keychain is unlocked

    path
        The path to the keychain for which will determine locked/unlocked status
    '''
    # Hell, even the security tool won't tell you (directly) if a keychain is unlocked ...
    status = __salt__['keychain.available'](path)

    if not status['usable']:
        raise salt.exceptions.CommandExecutionError('Error: No such keychain')

    return status['unlocked']