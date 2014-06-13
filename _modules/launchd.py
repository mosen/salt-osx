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
    from ServiceManagement import SMCopyAllJobDictionaries, \
        SMJobCopyDictionary, \
        kSMDomainSystemLaunchd, \
        kSMDomainUserLaunchd, \
        SMJobRemove, \
        SMJobSubmit

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
    error, status_ok = SMJobSubmit(kSMDomainSystemLaunchd, job_dict, None, error)

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
    error, status_ok = SMJobRemove(kSMDomainSystemLaunchd, label, None, False)

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



