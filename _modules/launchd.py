"""
List, query, submit and remove launchd jobs

:maintainer:    Mosen <mosen@github.com>
:maturity:      new
:depends:       objc, ServiceManagement, ctypes
:platform:      darwin
"""

from salt.utils.decorators import depends
import logging

log = logging.getLogger(__name__)

# Does not include per-user Launch Agents
LAUNCHD_DIRS = [
    '/Library/LaunchAgents',
    '/Library/LaunchDaemons',
    '/System/Library/LaunchAgents',
    '/System/Library/LaunchDaemons'
]

LAUNCHD_OVERRIDES = '/var/db/launchd.db/com.apple.launchd/overrides.plist'
LAUNCHD_OVERRIDES_PERUSER = '/var/db/launchd/com.apple.launchd.peruser.%d/overrides.plist'


try:
    from ctypes import *
    import objc

    # CoreFoundation Junk
    CFPath = '/System/Library/Frameworks/CoreFoundation.framework/Versions/Current/CoreFoundation'
    CF = CDLL(CFPath)

    CFRelease = CF.CFRelease
    CFRelease.restype = None
    CFRelease.argtypes = [c_void_p]

    kCFStringEncodingUTF8 = 0x08000100

    CFShow = CF.CFShow
    CFShow.argtypes = [c_void_p]
    CFShow.restype = None

    CFStringCreateWithCString = CF.CFStringCreateWithCString
    CFStringCreateWithCString.restype = c_void_p
    CFStringCreateWithCString.argtypes = [c_void_p, c_void_p, c_uint32]

    kCFAllocatorDefault = c_void_p()

    CFErrorCopyDescription = CF.CFErrorCopyDescription
    CFErrorCopyDescription.restype = c_void_p
    CFErrorCopyDescription.argtypes = [c_void_p]

    ServiceManagementPath = '/System/Library/Frameworks/ServiceManagement.framework/Versions/Current/ServiceManagement'
    ServiceManagement = CDLL(ServiceManagementPath)

    kSMRightBlessPrivilegedHelper = "com.apple.ServiceManagement.blesshelper"
    kSMRightModifySystemDaemons = "com.apple.ServiceManagement.daemons.modify"

    kSMDomainSystemLaunchd = c_void_p.in_dll(ServiceManagement,
                                             "kSMDomainSystemLaunchd")

    SMJobBless = ServiceManagement.SMJobBless
    SMJobBless.restype = c_bool
    SMJobBless.argtypes = [c_void_p, c_void_p, c_void_p, POINTER(c_void_p)]

    SMJobSubmit = ServiceManagement.SMJobSubmit
    SMJobSubmit.restype = c_bool
    SMJobSubmit.argtypes = [c_void_p, c_void_p, c_void_p, POINTER(c_void_p)]

    SMJobRemove = ServiceManagement.SMJobRemove
    SMJobRemove.restype = c_bool
    SMJobRemove.argtypes = [c_void_p, c_void_p, c_void_p, c_bool,
                            POINTER(c_void_p)]

    SMJobCopyDictionary = ServiceManagement.SMJobCopyDictionary
    SMJobCopyDictionary.restype = c_void_p
    SMJobCopyDictionary.argtypes = [c_void_p, c_void_p]


    class DaemonInstallException(Exception):
        """Error securely installing daemon."""





    class DaemonRemoveException(Exception):
        """Error removing existing daemon."""


    class DaemonVersionMismatchException(Exception):
        """Incompatible version of the daemon found."""

    def create_cfstr(s):
        """Creates a CFString from a python string.

        Note - because this is a "create" function, you have to CFRelease
        the returned string.
        """
        return CFStringCreateWithCString(kCFAllocatorDefault,
                                         s.encode('utf8'),
                                         kCFStringEncodingUTF8)

    has_imports = True
except ImportError:
    has_imports = False


__virtualname__ = 'launchd'


def __virtual__():
    '''
    Only load if the platform is correct and we can use PyObjC libs
    '''
    if __grains__.get('kernel') != 'Darwin':
        return False
    else:
        return __virtualname__


def _remove_job(authRef, job_label):
    """Call SMJobRemove to remove daemon.

    No return, raises on error.
    """
    desc_cfstr = None
    try:
        error = c_void_p()

        label_cfstr = create_cfstr(job_label)
        ok = SMJobRemove(kSMDomainSystemLaunchd,
                         label_cfstr,
                         authRef,
                         True,
                         byref(error))

        CFRelease(label_cfstr)

        if not ok:
            desc_cfstr = CFErrorCopyDescription(error)
            CFShow(desc_cfstr)
            raise DaemonRemoveException("SMJobRemove error (see above)")
    finally:
        if desc_cfstr:
            CFRelease(desc_cfstr)


def _submit_job(authRef, job_dict):
    """Call SMJobSubmit to submit a launchd job description.

    No return"""

    desc_cfstr = None
    cf_job_dict = job_dict

    try:
        error = c_void_p()

        ok = SMJobSubmit(kSMDomainSystemLaunchd,
                         cf_job_dict,  # objc bridges to NSDictionary bridges to CFDictionary
                         authRef,
                         byref(error))

        if not ok:
            desc_cfstr = CFErrorCopyDescription(error)
            CFShow(desc_cfstr)
            raise DaemonInstallException("SMJobSubmit error (see above)")

    finally:
        if desc_cfstr:
            CFRelease(desc_cfstr)


def _bless_helper(authRef, job_label):
    """Call SMJobBless to install a helper executable.

    No return, raises on error.
    """

    desc_cfstr = None

    try:
        error = c_void_p()

        label_cfstr = create_cfstr(job_label)
        ok = SMJobBless(kSMDomainSystemLaunchd,
                        label_cfstr,
                        authRef,
                        byref(error))
        CFRelease(label_cfstr)

        if not ok:
            desc_cfstr = CFErrorCopyDescription(error)
            CFShow(desc_cfstr)
            raise DaemonInstallException("SMJobBless error (see above)")

    finally:
        if desc_cfstr:
            CFRelease(desc_cfstr)


# def items(domain=u'system'):
#     '''
#     Get a sorted list of launchd job labels.
#
#     domain
#         The launchd context, 'user' or 'system', defaults to 'system'.
#
#     CLI Example:
#
#     .. code-block:: bash
#
#         salt '*' launchd.items [domain]
#     '''
#     try:
#         job_domain = kSMDomainSystemLaunchd if (domain == u'system') else kSMDomainUserLaunchd
#         job_dicts = SMCopyAllJobDictionaries(job_domain)
#     except Exception:
#         import traceback
#
#         log.debug("Error fetching job dictionaries for user domain")
#         log.debug(traceback.format_exc())
#         return False
#
#     job_labels = list()
#
#     for dict in job_dicts:
#         job_labels.append(dict.objectForKey_(u'Label'))
#
#     job_labels.sort()
#     return job_labels
#
#
# def info(label, domain=u'system'):
#     '''
#     Get information about a job via its label.
#
#     label
#         The launchd label for the job
#
#     domain
#         [Optional] The launchd context, 'user' or 'system', defaults to 'system'.
#
#     CLI Example:
#
#     .. code-block:: bash
#
#         salt '*' launchd.info <label> [domain]
#     '''
#     try:
#         job_domain = kSMDomainSystemLaunchd if (domain == u'system') else kSMDomainUserLaunchd
#         job_dict = SMJobCopyDictionary(job_domain, label)
#     except Exception:
#         import traceback
#
#         log.debug("Error fetching job definition for label: %s", label)
#         log.debug(traceback.format_exc())
#         return False
#
#     return job_dict
#
#
# def pidof(label, domain=u'system'):
#     '''
#     Get process id of a job via its label.
#
#     label
#         The launchd label for the job
#
#     domain
#         [Optional] The launchd context, 'user' or 'system', defaults to 'system'.
#     '''
#     try:
#         job_domain = kSMDomainSystemLaunchd if (domain == u'system') else kSMDomainUserLaunchd
#         job_dict = SMJobCopyDictionary(job_domain, label)
#     except Exception:
#         import traceback
#
#         log.debug("Error fetching job definition for label: %s", label)
#         log.debug(traceback.format_exc())
#         return False
#
#     return job_dict.objectForKey_(u'PID')
#
#
def load(name, persist=False):
    '''
    Load a launchd job by filename

    path
        The fully qualified path to a .plist launchd job description.

    persist
        true - persist the job by making disabled=false in launchd overrides.
        false - do not make the job permanent

    CLI Example:

    .. code-block:: bash

        salt '*' launchd.load <path> [persist]
    '''
    job_dict = __salt__['plist.read'](name)  # Gets a native NSCFDictionary

    try:
        authRef = __salt__['authorization.create'](kSMRightModifySystemDaemons)
        _submit_job(authRef, job_dict)

    except DaemonInstallException, e:
        log.error("Exception trying to install launchd job: %r" % e)
        raise e

    finally:
        __salt__['authorization.free'](authRef)


def unload(label, persist=False):
    '''
    Unload a launchd job by label

    path
        The fully qualified path to a .plist launchd job description.

    persist
        true - persist the job by making disabled=true in launchd overrides.
        false - do not make the job permanent

    CLI Example:

    .. code-block:: bash

        salt '*' launchd.unload <path> [persist]
    '''
    try:
        authRef = __salt__['authorization.create'](kSMRightModifySystemDaemons)
        _remove_job(authRef, label)

    except DaemonRemoveException, e:
        log.error("Exception trying to remove launchd job: %r" % e)
        raise e

    finally:
        __salt__['authorization.free'](authRef)



# Iterate through every plist in standard directories
# Find original plist value for Disabled key
# Find overridden value for key
def enabled(label, domain='system'):
    '''
    Get the status of the 'disabled' key for the given job (via original job plus overrides).
    If the job is enabled returns True, otherwise False. CURRENTLY ONLY WORKS AT SYSTEM LEVEL

    CLI Example:

    .. code-block:: bash

        salt '*' launchd.enabled <label> [domain='system']
    '''
    overrides = __salt__['plist.read'](LAUNCHD_OVERRIDES)

    # If override for job exists, there's no need to check the original job key for Disabled.
    if label in overrides:
        return overrides[label]['Disabled'] == False
    else:
        return 'Check original plist'



