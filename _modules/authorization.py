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
    from ctypes import *

    # Security Junk
    Security = CDLL('/System/Library/Frameworks/Security.framework/Versions/Current/Security')

    AuthorizationCreate = Security.AuthorizationCreate
    AuthorizationCreate.restype = c_int32
    AuthorizationCreate.argtypes = [c_void_p, c_void_p, c_int32, c_void_p]

    AuthorizationFree = Security.AuthorizationFree
    AuthorizationFree.restype = c_uint32
    AuthorizationFree.argtypes = [c_void_p, c_uint32]

    kAuthorizationFlagDefaults = 0
    kAuthorizationFlagInteractionAllowed = 1 << 0
    kAuthorizationFlagExtendRights = 1 << 1
    kAuthorizationFlagDestroyRights = 1 << 3
    kAuthorizationFlagPreAuthorize = 1 << 4

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


    class AuthorizationRights(Structure):
        """AuthorizationRights Struct"""
        _fields_ = [("count", c_uint32),
                    # * 1 here is specific to our use below
                    ("items", POINTER(AuthorizationItem))]


    class AuthUserCanceledException(Exception):
        """The user canceled the authorization."""


    class AuthFailedException(Exception):
        """The authorization faild for some reason."""


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

    # pylint: disable=W0201
    authItemBless = AuthorizationItem()
    authItemBless.name = right
    authItemBless.valueLength = 0
    authItemBless.value = None
    authItemBless.flags = 0

    authRights = AuthorizationRights()
    authRights.count = 1
    authRights.items = (AuthorizationItem * 1)(authItemBless)

    flags = (kAuthorizationFlagDefaults |
             kAuthorizationFlagInteractionAllowed |
             kAuthorizationFlagPreAuthorize |
             kAuthorizationFlagExtendRights)

    authRef = c_void_p()

    status = AuthorizationCreate(byref(authRights),
                                 kAuthorizationEmptyEnvironment,
                                 flags,
                                 byref(authRef))

    if status != errAuthorizationSuccess:

        if status == errAuthorizationInteractionNotAllowed:
            raise AuthFailedException("Authorization failed: "
                                      "interaction not allowed.")

        elif status == errAuthorizationDenied:
            raise AuthFailedException("Authorization failed: auth denied.")

        else:
            raise AuthUserCanceledException()

    if authRef is None:
        raise AuthFailedException("No authRef from AuthorizationCreate: %r"
                                  % status)
    return authRef


def free(authRef):
    """Free authorization reference"""
    AuthorizationFree(authRef, kAuthorizationFlagDestroyRights)