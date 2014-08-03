"""
OSX Authorization Framework Functionality

Mostly provided to allow other execution modules to call functions that require
elevated privileges.

Not required when calling a utility via cmd.run

:maintainer:    Mosen <mosen@github.com>
:maturity:      new
:depends:       objc,Foundation,Cocoa
:platform:      darwin
"""

import logging

log = logging.getLogger(__name__)

HAS_LIBS = False
try:
    # A large section of the Authorization services code has been lifted from
    # the now deprecated Ubuntu One installer by Canonical, Licensed GPLv3
    from ctypes import CDLL, Structure, POINTER, c_char_p, c_size_t, \
        c_void_p, c_uint32, pointer, byref

    # Security Junk
    Security = CDLL('/System/Library/Frameworks/Security.framework/Versions/Current/Security')

    class OpaqueType(Structure):
        pass

    OpaqueTypeRef = POINTER(OpaqueType)

    AuthorizationRef = OpaqueTypeRef
    CFErrorRef = OpaqueTypeRef

    kSMRightModifySystemDaemons   = "com.apple.ServiceManagement.daemons.modify"
    kSMRightBlessPrivilegedHelper = "com.apple.ServiceManagement.blesshelper"

    AuthorizationCreate = Security.AuthorizationCreate
    AuthorizationCopyRights = Security.AuthorizationCopyRights

    AuthorizationFree = Security.AuthorizationFree
    AuthorizationFree.restype = c_uint32
    AuthorizationFree.argtypes = [c_void_p, c_uint32]

    kAuthorizationFlagDefaults = 0
    kAuthorizationFlagInteractionAllowed = (1 << 0)
    kAuthorizationFlagExtendRights = (1 << 1)
    kAuthorizationFlagPartialRights = (1 << 2)
    kAuthorizationFlagDestroyRights = (1 << 3)
    kAuthorizationFlagPreAuthorize = (1 << 4)

    kAuthorizationEmptyEnvironment = None

    errAuthorizationSuccess = 0
    errAuthorizationDenied = -60005
    errAuthorizationCanceled = -60006
    errAuthorizationInteractionNotAllowed = -60007

    class AuthorizationItem(Structure):
        """AuthorizationItem Struct"""
        _fields_ = [("name", c_char_p),
                    ("valueLength", c_uint32),
                    ("value", c_void_p),
                    ("flags", c_uint32)]


    class AuthorizationItemSet(Structure):
        _fields_ = [('count', c_uint32),
                    ('items', POINTER(AuthorizationItem)),
                    ]

    class AuthUserCanceledException(Exception):
        """The user canceled the authorization."""


    class AuthFailedException(Exception):
        """The authorization failed for some reason."""


    HAS_LIBS = True
except ImportError:
    log.debug('Execution module not suitable because one or more imports failed.')

__virtualname__ = 'authorization'


def __virtual__():
    '''
    Only load if the platform is correct and we can use PyObjC libs
    '''
    if __grains__.get('kernel') != 'Darwin':
        return False

    if not HAS_LIBS:
        return False

    else:
        return __virtualname__


def create(right):
    """Get authorization with named right"""

    # Create Reference
    authref = AuthorizationRef()
    status = AuthorizationCreate(None,
                                 kAuthorizationEmptyEnvironment,
                                 kAuthorizationFlagDefaults,
                                 byref(authref))


    # Declare and Request Rights
    right_set = (AuthorizationItem*1)()
    right_set[0].name = right

    rights = AuthorizationItemSet()
    rights.count = 1
    rights.items = pointer(right_set[0])

    flags = (kAuthorizationFlagDefaults |
             kAuthorizationFlagInteractionAllowed |
             kAuthorizationFlagPreAuthorize |
             kAuthorizationFlagExtendRights)

    given_rights = AuthorizationItemSet()
    status_ok = AuthorizationCopyRights(authref, byref(rights), kAuthorizationEmptyEnvironment, flags, byref(given_rights))

    if status_ok == 0:
        log.info("Got requested rights from Authorization services")
        return authref
    else:
        return None


def free(authref):
    """Free authorization reference"""
    AuthorizationFree(authref, kAuthorizationFlagDestroyRights)