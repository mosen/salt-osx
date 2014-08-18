'''
remote management (ard) service state

configuration of the remote management service and privileges.

 .. code-block:: yaml

    system:
      ard:
        - managed
        - enabled: True
        - allow_all_users: True
        - all_users_privs: "-1073741569"
        - enable_menu_extra: True
        - enable_dir_logins: True
        - directory_groups:
            - ard_users
            - ard_admins
        - enable_legacy_vnc: True
        - vnc_password: password
        - allow_vnc_requests: True
        - allow_wbem_requests: True
        - users:
          - joe: "-1073741569"
          - sally: "-1073741569"
'''
import salt.utils

__virtualname__ = 'ard'

def __virtual__():
    """Only load on OSX"""
    return __virtualname__ if salt.utils.is_darwin() else False

_PATHS = {
    'preferences':'/Library/Preferences/com.apple.RemoteManagement.plist'
}

_ATTR_TO_KEY = {
    'allow_all_users':     'ARD_AllLocalUsers',
    'all_users_privs':     'ARD_AllLocalUsersPrivs',
    'enable_menu_extra':   'LoadRemoteManagementMenuExtra',
    'enable_dir_logins':   'DirectoryGroupLoginsEnabled',
    'directory_groups':    'DirectoryGroupList',
    'enable_legacy_vnc':   'VNCLegacyConnectionsEnabled',
    'allow_vnc_requests':  'ScreenSharingReqPermEnabled',
    'allow_wbem_requests': 'WBEMIncomingAccessEnabled'
}

_KEY_TO_ATTR = {
    'ARD_AllLocalUsers': 'allow_all_users',
    'ARD_AllLocalUsersPrivs': 'all_users_privs',
    'LoadRemoteManagementMenuExtra': 'enable_menu_extra',
    'DirectoryGroupLoginsEnabled': 'enable_dir_logins',
    'DirectoryGroupList': 'directory_groups',
    'VNCLegacyConnectionsEnabled': 'enable_legacy_vnc',
    'ScreenSharingReqPermEnabled': 'allow_vnc_requests',
    'WBEMIncomingAccessEnabled': 'allow_wbem_requests'
}

def managed(name, enabled=True, **kwargs):
    '''
    Enforce "remote management" (ARD) service settings.

    name
        This is mostly irrelevant since the settings are system wide.

    enabled : True
        Whether the remote management service is active and should start on boot.

    allow_all_users
        Should all local users be allowed to connect?

    all_users_privs
        Privileges applied if `allow_all_users` was enabled.

    enable_menu_extra
        Whether or not to enable the ard menu extra

    enable_dir_logins
        Whether or not to allow logins from directory users

    directory_groups
        List of directory groups that may access this service

    enable_legacy_vnc
        Whether to allow legacy VNC connections

    vnc_password
        The VNC plain text password for connecting. VERY INSECURE.

    allow_vnc_requests
        Whether people may request permission to share the screen using vnc

    allow_wbem_requests
        Whether to allow WBEM requests

    users
        List of users and their privileges
    '''
    ret = {'name':name, 'changes':{}, 'result':False, 'comment':''}

    changes = {'old':{}, 'new':{}}

    isEnabled = __salt__['ard.active']()

    if enabled != isEnabled:
        changes['old']['enabled'] = isEnabled
        changes['new']['enabled'] = enabled

    preferences = {_ATTR_TO_KEY[k]:v for k,v in kwargs.iteritems() if k in _ATTR_TO_KEY}

    if __opts__['test'] == True:
        prefDiff = __salt__['plist.write_keys'](_PATHS['preferences'], preferences, True)
        ret['result'] = None
    else:
        prefDiff = __salt__['plist.write_keys'](_PATHS['preferences'], preferences)
        ret['result'] = True

    for k, v in prefDiff.iteritems():
        changes['new'][_KEY_TO_ATTR[k]] = v

    if len(changes['new'].keys()) == 0:
        ret['result'] = None
        ret['comment'] = 'No changes required'
    else:
        if 'enabled' in changes['new']:
            if changes['new']['enabled']:
                __salt__['ard.activate']()
                ret['comment'] = 'Remote management enabled'
            else:
                __salt__['ard.deactivate']()
                ret['comment'] = 'Remote management disabled'

        ret['changes'] = changes

    return ret

