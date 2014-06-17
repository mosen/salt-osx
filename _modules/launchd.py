"""
List or read launchd job details

:maintainer:    Mosen <mosen@github.com>
:maturity:      new
:depends:       objc,ServiceManagement
:platform:      darwin
"""

from salt.utils.decorators import depends
import logging

log = logging.getLogger(__name__)

try:
    from ctypes import CDLL, Structure, POINTER, c_char_p, c_size_t, c_void_p, c_uint32, pointer, byref
    from ServiceManagement import SMCopyAllJobDictionaries, \
        SMJobCopyDictionary, \
        kSMDomainSystemLaunchd, \
        kSMDomainUserLaunchd, \
        SMJobRemove, \
        SMJobSubmit

    Security = CDLL('/System/Library/Frameworks/Security.framework/Versions/Current/Security')

    class OpaqueType(Structure):
        pass

    OpaqueTypeRef = POINTER(OpaqueType)

    AuthorizationRef = OpaqueTypeRef

    kSMRightModifySystemDaemons   = "com.apple.ServiceManagement.daemons.modify"
    kSMRightBlessPrivilegedHelper = "com.apple.ServiceManagement.blesshelper"

    kAuthorizationEmptyEnvironment = None

    kAuthorizationFlagDefaults = 0
    kAuthorizationFlagInteractionAllowed = (1 << 0)
    kAuthorizationFlagExtendRights = (1 << 1)
    kAuthorizationFlagPartialRights = (1 << 2)
    kAuthorizationFlagDestroyRights = (1 << 3)
    kAuthorizationFlagPreAuthorize = (1 << 4)

    class AuthorizationItem(Structure):
        _fields_ = [('name', c_char_p),
                    ('valueLength', c_size_t),
                    ('value', c_void_p),
                    ('flags', c_uint32),
                    ]

    class AuthorizationItemSet(Structure):
        _fields_ = [('count', c_uint32),
                    ('items', POINTER(AuthorizationItem)),
                    ]

    AuthorizationCreate = Security.AuthorizationCreate
    AuthorizationCopyRights = Security.AuthorizationCopyRights
    AuthorizationFreeItemSet = Security.AuthorizationFreeItemSet
    AuthorizationFree = Security.AuthorizationFree

    has_imports = True
except ImportError:
    has_imports = False

# Does not include per-user Launch Agents
LAUNCHD_DIRS = [
    '/Library/LaunchAgents',
    '/Library/LaunchDaemons',
    '/System/Library/LaunchAgents',
    '/System/Library/LaunchDaemons'
]

LAUNCHD_OVERRIDES = '/var/db/launchd.db/com.apple.launchd/overrides.plist'
LAUNCHD_OVERRIDES_PERUSER = '/var/db/launchd/com.apple.launchd.peruser.%d/overrides.plist'




__virtualname__ = 'launchd'


def __virtual__():
    '''
    Only load if the platform is correct and we can use PyObjC libs
    '''
    if __grains__.get('kernel') != 'Darwin':
        return False
    else:
        return __virtualname__


def _get_auth(right):
    '''
    Get a single authorization right from auth services framework.
    '''
    authref = AuthorizationRef()
    result = AuthorizationCreate(None, kAuthorizationEmptyEnvironment, kAuthorizationFlagDefaults, byref(authref))

    right_set = (AuthorizationItem*1)()
    right_set[0].name = right
    rights = AuthorizationItemSet()
    rights.count = 1
    rights.items = pointer(right_set)

    # No interaction allowed
    flags = kAuthorizationFlagDefaults | kAuthorizationFlagPreAuthorize | kAuthorizationFlagExtendRights

    given_rights = AuthorizationItemSet()

    result = AuthorizationCopyRights(authref, byref(rights), kAuthorizationEmptyEnvironment, flags, byref(given_rights))
    return (authref, given_rights) if result == 0 else False


def _dealloc_auth(authref):
    '''
    Deallocate AuthorizationRef
    '''
    result = AuthorizationFree(authref, kAuthorizationFlagDefaults | kAuthorizationFlagDestroyRights)
    return True if result == 0 else False


def _dealloc_rights(rights):
    '''
    Deallocate authorization rights
    '''
    result = AuthorizationFreeItemSet(rights)
    return True if result == 0 else False


def items(domain=u'system'):
    '''
    Get a sorted list of launchd job labels.

    domain
        The launchd context, 'user' or 'system', defaults to 'system'.

    CLI Example:

    .. code-block:: bash

        salt '*' launchd.items [domain]
    '''
    try:
        job_domain = kSMDomainSystemLaunchd if (domain == u'system') else kSMDomainUserLaunchd
        job_dicts = SMCopyAllJobDictionaries(job_domain)
    except Exception:
        import traceback

        log.debug("Error fetching job dictionaries for user domain")
        log.debug(traceback.format_exc())
        return False

    job_labels = list()

    for dict in job_dicts:
        job_labels.append(dict.objectForKey_(u'Label'))

    job_labels.sort()
    return job_labels


def info(label, domain=u'system'):
    '''
    Get information about a job via its label.

    label
        The launchd label for the job

    domain
        [Optional] The launchd context, 'user' or 'system', defaults to 'system'.

    CLI Example:

    .. code-block:: bash

        salt '*' launchd.info <label> [domain]
    '''
    try:
        job_domain = kSMDomainSystemLaunchd if (domain == u'system') else kSMDomainUserLaunchd
        job_dict = SMJobCopyDictionary(job_domain, label)
    except Exception:
        import traceback

        log.debug("Error fetching job definition for label: %s", label)
        log.debug(traceback.format_exc())
        return False

    return job_dict


def pidof(label, domain=u'system'):
    '''
    Get process id of a job via its label.

    label
        The launchd label for the job

    domain
        [Optional] The launchd context, 'user' or 'system', defaults to 'system'.
    '''
    try:
        job_domain = kSMDomainSystemLaunchd if (domain == u'system') else kSMDomainUserLaunchd
        job_dict = SMJobCopyDictionary(job_domain, label)
    except Exception:
        import traceback

        log.debug("Error fetching job definition for label: %s", label)
        log.debug(traceback.format_exc())
        return False

    return job_dict.objectForKey_(u'PID')


@depends('plist')
def load(name, persist=False):
    '''
    Load a launchd job by filename - TODO needs to request auth rights.

    path
        The fully qualified path to a .plist launchd job description.

    persist
        true - persist the job by making disabled=false in launchd overrides.
        false - do not make the job permanent

    CLI Example:

    .. code-block:: bash

        salt '*' launchd.load <path> [persist]
    '''
    job_dict = __salt__['plist.read'](name)
    authref, rights = _get_auth(kSMRightModifySystemDaemons)
    error, status_ok = SMJobSubmit(kSMDomainSystemLaunchd, job_dict, authref)

    _dealloc_rights(rights)
    _dealloc_auth(authref)

    if not status_ok:
        import traceback

        log.debug("Error submitting launchd job: %s, error: %s", name, error)
        log.debug(traceback.format_exc())
        return False
    else:
        return True


def unload(label, persist=False):
    '''
    Unload a launchd job by label - TODO needs to request auth rights.

    path
        The fully qualified path to a .plist launchd job description.

    persist
        true - persist the job by making disabled=true in launchd overrides.
        false - do not make the job permanent

    CLI Example:

    .. code-block:: bash

        salt '*' launchd.unload <path> [persist]
    '''
    authref, rights = _get_auth(kSMRightModifySystemDaemons)
    error, status_ok = SMJobRemove(kSMDomainSystemLaunchd, label, None, False)

    _dealloc_rights(rights)
    _dealloc_auth(authref)

    if not status_ok:
        import traceback

        log.debug("Error removing launchd job: %s, error: %s", label, error)
        log.debug(traceback.format_exc())
        return False
    else:
        return True


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



