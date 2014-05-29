"""List or read launchd job details

Does not manage:
- StartupItems (/Library/StartupItems), which will be deprecated.
- LoginItems helper bundles
- Launch Services loginitems using shared file list.
- LoginHook via loginwindow prefs.
- Authorisation database mechanisms/Pre login mechanisms.



:maintainer:    Mosen <mosen@github.com>
:maturity:      new
:depends:       objc
:platform:      darwin
"""

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


__virtualname__ = 'launchd'


def __virtual__():
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

    print(job_dict)

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

