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
    return __virtualname__ if salt.utils.is_darwin() else False


_PATHS = {
    'preferences': '/Library/Preferences/com.apple.RemoteManagement.plist'
}

# 'all_users_privs':     'ARD_AllLocalUsersPrivs',
_ATTR_TO_KEY = {
    'allow_all_users': 'ARD_AllLocalUsers',
    'enable_menu_extra': 'LoadRemoteManagementMenuExtra',
    'enable_dir_logins': 'DirectoryGroupLoginsEnabled',
    'directory_groups': 'DirectoryGroupList',
    'enable_legacy_vnc': 'VNCLegacyConnectionsEnabled',
    'allow_vnc_requests': 'ScreenSharingReqPermEnabled',
    'allow_wbem_requests': 'WBEMIncomingAccessEnabled'
}

_KEY_TO_ATTR = {y: x for x, y in _ATTR_TO_KEY.iteritems()}


def managed(name, enabled=True, **kwargs):
    '''
    Enforce "remote management" (ARD) service settings.
    per-user privileges are set via the ard.privileges state.

    name
        This is mostly irrelevant since the settings are system wide.

    enabled : True
        Whether the remote management service is active and should start on boot.

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

    # Not all property list values can simply be compared, some values need munging before the comparison. eg.privileges
    current_plist = __salt__['plist.read'](_PATHS['preferences'])
    service_is_enabled = __salt__['ard.active']()
    all_users_privs = __salt__['ard.naprivs_list'](current_plist['ARD_AllLocalUsersPrivs'])
    vnc_password = __salt__['ard.vncpw']()

    if enabled != service_is_enabled:
        changes['old']['enabled'] = service_is_enabled
        changes['new']['enabled'] = enabled

    if 'all_users_privs' in kwargs and set(all_users_privs) != set(kwargs['all_users_privs']):
        changes['old']['all_users_privs'] = all_users_privs
        changes['new']['all_users_privs'] = kwargs['all_users_privs']

    if 'vnc_password' in kwargs and vnc_password != kwargs['vnc_password']:
        changes['old']['vnc_password'] = vnc_password
        changes['new']['vnc_password'] = kwargs['vnc_password']

    current_prefs = {_KEY_TO_ATTR[k]: v for k, v in current_plist.iteritems() if k in _KEY_TO_ATTR}
    desired_prefs = {k: v for k, v in kwargs.iteritems() if k in _ATTR_TO_KEY}
    changed_prefs = {k: v for k, v in desired_prefs.iteritems() if k not in current_prefs or current_prefs[k] != v}

    if __opts__['test'] == True:
        for k, v in changed_prefs.iteritems():
            changes['old'][k] = current_prefs[k]
            changes['new'][k] = v

        ret['changes'] = changes
        ret['result'] = None
    else:
        ret['result'] = True

    if len(changes['new'].keys()) == 0:
        ret['result'] = None
        ret['comment'] = 'No changes required'
    else:
        if 'enabled' in changes['new']:
            if changes['new'].get('vnc_password', False):
                __salt__['ard.set_vncpw'](changes['new']['vnc_password'])

            if changed_prefs:
                for k, v in changed_prefs.iteritems():
                    current_plist[_ATTR_TO_KEY[k]] = v

                if 'all_users_privs' in changes['new']:
                    all_users_naprivs = __salt__['ard.list_naprivs'](changes['new']['all_users_privs'].join(','))
                    log.debug('Setting remote management all users privilege to: {0}'.format(all_users_naprivs))
                    current_plist['ARD_AllLocalUsersPrivs'] = all_users_naprivs

                __salt__['plist.write'](_PATHS['preferences'], current_plist)

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

    old_privs = __salt__['ard.user'](name).get(name, list())

    if set(old_privs) == set(privs['list']):
        ret['comment'] = 'No changes to remote management privileges required.'
    else:
        changes['old'] = old_privs
        changes['new'] = privs['list']

    if __opts__['test'] == True:
        ret['changes'] = changes if changes else dict()

        if changes:
            ret['comment'] = 'Remote management privileges for {0} would have been changed.'.format(name)
        else:
            ret['comment'] = 'No changes will be made to remote management privileges for {0}'.format(name)

        ret['result'] = None
    else:
        if changes['new']:
            success = __salt__['ard.set_user_privs'](name, ','.join(privs['list']))
            ret['changes'] = changes
            ret['result'] = success
        else:
            ret['result'] = None

    return ret