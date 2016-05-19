"""
Retrieve information about Apple's ColorSync settings and profiles

:maintainer:    Mosen <mosen@github.com>
:maturity:      new
:depends:       objc,Foundation,Cocoa
:platform:      darwin
"""
from __future__ import absolute_import



import salt.utils
from salt.exceptions import SaltInvocationError

__virtualname__ = 'colorsync'


import logging
log = logging.getLogger(__name__)


HAS_LIBS = False
try:
    from ctypes import *
    ColorSync = CDLL('/System/Library/Frameworks/ApplicationServices.framework/Frameworks/ColorSync.framework/Versions/Current/ColorSync')



    HAS_LIBS = True
except ImportError:
    log.debug('Execution module not suitable because one or more imports failed.')


class _FSSpec(Structure):
    """Identifies a Mac OS file or directory"""
    _fields_ = [
        ("vRefNum", c_short),
        ("parID", c_long),
        ("name", c_char_p)
    ]

class _CMHandleLocation(Structure):
    pass

class _CMPtrLocation(Structure):
    pass

class _CMProcedureLocation(Structure):
    pass

class _CMPathLocation(Structure):
    pass

class _CMBufferLocation(Structure):
    pass


class _CMFileLocation(Structure):
    """Contains a file specification for a profile stored in a disk file"""
    _fields_ = [
        ("spec", _FSSpec)
    ]

class _CMProfLoc(Union):
    """Defines a union that identifies the location of a profile."""
    _fields_ = [
        ("fileLoc", _CMFileLocation),
        ("handleLoc", _CMHandleLocation),
        ("ptrLoc", _CMPtrLocation),
        ("procLoc", _CMProcedureLocation),
        ("pathLoc", _CMPathLocation),
        ("bufferLoc", _CMBufferLocation)
    ]

class _CMProfileLocation(Structure):
    """Contains profile location information"""
    _fields_ = [
        ("locType", c_short),
        ("u", _CMProfLoc)
    ]

class _CM2Header(Structure):
    """Information to support the header format of ICC v2.x Profiles"""
    _fields_ = [
        ("size", c_size_t),
        ("CMMType", c_char * 4),
        ("profileVersion", c_int),
        ("profileClass", c_char * 4),
        ("dataColorSpace", c_char * 4),
        ("profileConnectionSpace", c_char * 4),
        ("dateTime", POINTER(c_char)),
        ("CS2profileSignature", c_char * 4)
    ]

class _CMProfileIterateData(Structure):
    """Iterator data for ColorSync"""
    _fields_ = [
        ("dataVersion", c_int),
        ("header", _CM2Header),
        ("code", c_int16),
        ("name", c_char * 255),
        ("location", _CMProfileLocation),
        ("uniCodeNameCount", c_int32),
        ("uniCodeName", c_char_p),
        ("asciiName", c_char_p),
        ("makeAndModel", c_char_p),
        ("digest", c_char_p)
    ]

CMDeviceClasses = {'scnr': 'Scanner', 'cmra': 'Camera', 'mntr': 'Monitor', 'prtr': 'Printer', 'pruf': 'Proofer'}

class _CMDeviceScope(Structure):
    """
    .. _CMDeviceScope: https://developer.apple.com/library/mac/documentation/GraphicsImaging/Reference/ColorSync_Manager/index.html#//apple_ref/c/tdef/CMDeviceScope
    """
    _fields_ = [
        ("deviceUser", c_void_p),
        ("deviceHost", c_void_p)
    ]

class _CMDeviceInfo(Structure):
    _fields_ = [
        ("dataVersion", c_int),
        ("deviceClass", c_char * 4),
        ("deviceID", c_uint32),
        ("deviceScope", _CMDeviceScope),
        ("deviceState", c_uint32),
        ("defaultProfileID", c_uint32),
        ("deviceName", c_void_p),  # CFDictionaryRef
        ("profileCount", POINTER(c_uint32)),
        ("reserved", c_uint32),
    ]

class _NCMDeviceProfileInfo(Structure):
    _fields_ = [
        ("dataVersion", c_uint32),
        ("profileID", c_uint32),
        ("profileLoc", _CMProfileLocation),
        ("profileName", c_void_p),  # CFDictionaryRef
        ("profileScope", _CMDeviceScope),
        ("reserved", c_uint32)
    ]


CMProfileIterateProcPtr = CFUNCTYPE(c_int, POINTER(_CMProfileIterateData), POINTER(c_void_p))

CMIterateDeviceProfileProcPtr = CFUNCTYPE(c_void_p, c_void_p, c_void_p)
CMIterateDeviceProfileProcPtr.restype = c_void_p

def cb(device, profile, ref):
    log.error("called me")
    return None

cbcb = CMIterateDeviceProfileProcPtr(cb)

def devices():
    '''
    List ColorSync Devices
    :return:
    '''
    seed = 0
    profile_count = 0


    err = ColorSync.CMIterateDeviceProfiles(cbcb, seed, profile_count, 0, None)

    log.error(err)
    log.warning(profile_count)
