'''
remote management (ard) service state

configuration of the remote management service and privileges.

 .. code-block:: yaml

    system:
      ard:
        - managed
        - enabled: True
        - allow_all_users: True
        - all_users_privs: none
        - enable_menu_extra: True
        - enable_dir_logins: True
        - directory_groups:
            - ard_users
            - ard_admins
        - enable_legacy_vnc: True
        - vnc_password: password
        - allow_vnc_requests: True
        - allow_wbem_requests: True

    admin:
      ard.privileges:
        list:
          - observe_control
          - text
          - copy
          - launch
          - observe_hidden

'''
import logging
import salt.utils

log = logging.getLogger(__name__)

__virtualname__ = 'ard'


def __virtual__():
    """Only load on OSX"""
    return __virtualname__ if salt.utils.platform.is_darwin() else False


_PREF_DOMAIN = 'com.apple.RemoteManagement'

# These keys dont require any munging, just comparison against desired state.
_ATTR_TO_KEY = {
    'allow_all_users': 'ARD_AllLocalUsers',
    'enable_menu_extra': 'LoadRemoteManagementMenuExtra',
    'enable_dir_logins': 'DirectoryGroupLoginsEnabled',
    'enable_legacy_vnc': 'VNCLegacyConnectionsEnabled',
    'allow_vnc_requests': 'ScreenSharingReqPermEnabled',
    'allow_wbem_requests': 'WBEMIncomingAccessEnabled'
}

_KEY_TO_ATTR = {y: x for x, y in _ATTR_TO_KEY.items()}


def managed(name, enabled=None, **kwargs):
    '''
    Enforce "remote management" (ARD) service settings.
    per-user privileges are set via the ard.privileges state.

    name
        This is mostly irrelevant since the settings are system wide.

    enabled : None
        Whether the remote management service is active and should start on boot. If this param is
        omitted, the service will not be enabled or disabled.

    allow_all_users
        Should all local users be allowed to connect?

    all_users_privs
        Privileges applied if `allow_all_users` was enabled. See execution module ``ard.set_user_privs`` for options.

    enable_menu_extra
        Whether or not to enable the ard menu extra

    enable_dir_logins
        Whether or not to allow logins from directory users

    directory_groups
        List of directory groups that may access this service

    enable_legacy_vnc
        Whether to allow legacy VNC connections. Not recommended because password is stored insecurely.

    vnc_password
        The VNC plain text password for connecting. Not recommended because password is stored insecurely.

    allow_vnc_requests
        Whether people may request permission to share the screen using vnc

    allow_wbem_requests
        Whether to allow WBEM requests
    '''
    ret = {'name': name, 'changes': {}, 'result': False, 'comment': ''}
    changes = {'old': {}, 'new': {}}

    service_is_enabled = __salt__['ard.active']()
    # Not all values can simply be compared, some values need munging before the comparison. eg.privileges
    current_prefs = __salt__['prefs.list'](_PREF_DOMAIN, user='any', host='any', values=True)
    if 'ARD_AllLocalUsersPrivs' in current_prefs:
        all_users_privs = __salt__['ard.naprivs_list'](current_prefs['ARD_AllLocalUsersPrivs'])
    else:
        all_users_privs = []

    vnc_password = __salt__['ard.vncpw']()
    directory_groups = current_prefs.get('DirectoryGroupList', [])

    if enabled is not None and enabled != service_is_enabled:
        changes['old']['enabled'] = service_is_enabled
        changes['new']['enabled'] = enabled

    if 'all_users_privs' in kwargs and set(all_users_privs) != set(kwargs['all_users_privs']):
        changes['old']['all_users_privs'] = all_users_privs
        changes['new']['all_users_privs'] = kwargs['all_users_privs']

    if 'vnc_password' in kwargs and vnc_password != kwargs['vnc_password']:
        changes['old']['vnc_password'] = vnc_password
        changes['new']['vnc_password'] = kwargs['vnc_password']

    if 'directory_groups' in kwargs and set(directory_groups) != set(kwargs['directory_groups']):
        changes['old']['directory_groups'] = list(directory_groups)
        changes['new']['directory_groups'] = kwargs['directory_groups']

    desired_prefs = {_ATTR_TO_KEY[k]: v for k, v in kwargs.items() if k in _ATTR_TO_KEY}
    prefs_to_set = {k: v for k, v in desired_prefs.items() if v != current_prefs[k]}
    incorrect_prefs = {k: current_prefs[k] for k in prefs_to_set}
    if prefs_to_set:
        changes['old'].update(incorrect_prefs)
        changes['new'].update(prefs_to_set)

    if __opts__['test'] == True:
        ret['changes'] = changes
        ret['result'] = None

    else:
        ret['result'] = True

        if len(changes['new']) == 0:
            ret['comment'] = 'No changes required'
        else:
            if 'vnc_password' in changes['new']:
                __salt__['ard.set_vncpw'](changes['new']['vnc_password'])

            if 'all_users_privs' in changes['new']:
                all_users_naprivs = __salt__['ard.list_naprivs'](
                    ','.join(changes['new']['all_users_privs']))
                log.debug('Setting remote management all users privilege to: {0}'.format(
                    all_users_naprivs))
                prefs_to_set['ARD_AllLocalUsersPrivs'] = str(all_users_naprivs)

            if 'directory_groups' in changes['new']:
                prefs_to_set['DirectoryGroupList'] = changes['new']['directory_groups']

            if prefs_to_set:
                log.debug('Attempting to write new Remote Management preferences: {0}'.format(
                    prefs_to_set))
                for k, v in prefs_to_set.items():
                    __salt__['prefs.set'](
                        name=k, value=v, domain=_PREF_DOMAIN, user='any', host='any')

            if 'enabled' in changes['new']:
                if changes['new']['enabled']:
                    __salt__['ard.activate']()
                    ret['comment'] = 'Remote management enabled'
                else:
                    __salt__['ard.deactivate']()
                    ret['comment'] = 'Remote management disabled'

            ret['changes'] = changes

    return ret


def privileges(name, **privs):
    '''
    Manage remote management privileges for a given local directory user.
    '''
    ret = {'name': name, 'changes': {}, 'result': False, 'comment': ''}

    changes = {'old': {}, 'new': {}}

    current_privileges = __salt__['ard.user_privs'](name)

    if current_privileges is False:
        ret['comment'] = 'Attempted to modify privileges for a non existent user: {0}'.format(name)
        ret['result'] = False
        return ret

    old_privs = current_privileges[name] if current_privileges is not None else list()

    if set(old_privs) == set(privs['list']):
        ret['comment'] = 'Remote management privileges for {0} are in the correct state'.format(name)
    else:
        changes['old'] = old_privs
        changes['new'] = privs['list']

    if __opts__['test'] == True:
        ret['changes'] = changes if changes else dict()

        if changes:
            ret['comment'] = 'Remote management privileges for {0} would have been changed.'.format(name)
            ret['result'] = None
        else:
            ret['comment'] = 'Remote management privileges for {0} are in the correct state'.format(name)
            ret['result'] = True
    else:
        if changes['new']:
            success = __salt__['ard.set_user_privs'](name, ','.join(privs['list']))
            ret['changes'] = changes
            ret['result'] = success
        else:
            ret['result'] = True

    return ret
