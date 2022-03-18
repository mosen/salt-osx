# -*- coding: utf-8 -*-
"""Modules to interact with crowdstrike on macOS."""
import os
import pathlib
import plistlib

import salt.utils.platform
from Foundation import NSBundle
from salt.exceptions import CommandExecutionError

# Define the module's virtual name
__virtualname__ = 'crowdstrike'

__func_alias__ = {
    'license_': 'license',
}


def __virtual__():
    """Only for macOS with launchctl."""
    if not salt.utils.platform.is_darwin():
        return (
            False,
            'Failed to load the crowdstrike module. Only available on macOS systems.',
        )

    if (not os.path.exists('/Library/CS/falconctl') and
            not os.path.exists('/Applications/Falcon.app/Contents/Resources/falconctl')):
        return (
            False,
            'Failed to load the crowdstrike module. Required binary not found: /Library/CS/falconctl',
        )

    return __virtualname__


def system_extension():
    """Returns whether or not CrowdStrike should be using a System
    Extension.

    :return: True if it should be using a system extension otherwise False.

    :rtype: bool

    .. code-block:: bash

        salt '*' crowdstrike.system_extension
    """
    if __grains__['osmajorrelease'] >= 11:
        return True
    return False


def falconctl_path():
    """Returns a path to where `falconctl` is on the system. First looks
    for the v6 location, then older paths.

    :return: Full path to ``falconctl``.

    :rtype: str

    .. code-block:: bash

        salt '*' crowdstrike.falconctl_path
    """
    falconctl6 = '/Applications/Falcon.app/Contents/Resources/falconctl'
    return falconctl6 if os.path.exists(falconctl6) else '/Library/CS/falconctl'


def falcon_dir():
    """Returns a path to where the Crowdstrike directory is on the
    system. First looks for the v6 location, then older paths.

    :return: Full path to ``falconctl``.

    :rtype: str

    .. code-block:: bash

        salt '*' crowdstrike.falconctl_path
    """
    falcondir6 = '/Library/Application Support/CrowdStrike/Falcon/'
    return falcondir6 if os.path.exists(falcondir6) else '/Library/CS/'


def falconctl(sub_cmd, *args, **kwargs):
    """A wrapper for CrowdStrikes ``falconctl``.

    Looks for ``falconctl`` in the following places.

    Passes all kwargs to the lower level salt.cmd.run_all.

    Set return_stdout to True in kwargs to return the stdout of the command.

    .. code-block:: bash

        /Applications/Falcon.app/Contents/Resources/falconctl
        /Library/CS/falconctl

    :param str sub_cmd: the subcommand of ``falconctl`` to use.

    :param str args: any additional arguments to pass to ``falconctl``.

    :return: A boolean or standard out of the command.

    :rtype: bool, str

    .. code-block:: bash

        salt '*' crowdstrike.falconctl load
    """
    falconctl = __salt__['crowdstrike.falconctl_path']()
    # Construct command
    cmd = [falconctl, sub_cmd]
    cmd.extend(args)

    ret = __salt__['cmd.run_all'](cmd, ignore_retcode=True, **kwargs)
    # Raise an error or return successful result
    if ret['retcode']:
        out = f'Command Failed: {cmd}.\n'
        out += f"stdout: {ret['stdout']}\n"
        out += f"stderr: {ret['stderr']}\n"
        out += f"retcode: {ret['retcode']}"
        raise CommandExecutionError(out)

    return True if not kwargs.get('return_stdout') else ret['stdout']


def falconctl_plist():
    """return the falconctl stats as a plist to stdout.

    :return: return the plist version of falconctl stats

    :rtype: str

    .. code-block:: bash
        salt '*' crowdstrike.falconctl_plist
    """
    return __salt__['crowdstrike.falconctl']('stats', '--plist', timeout=30, return_stdout=True)


def load():
    """Attempts to load CrowdStrike Falcon.

    :return: A Boolean if successfully unloaded otherwise CommandExecutionError.

    :rtype: bool

    .. code-block:: bash
        salt '*' crowdstrike.load
    """
    return __salt__['crowdstrike.falconctl']('load', timeout=30)


def unload():
    """Attempts to unload CrowdStrike Falcon.

    :return: A Boolean if successfully unloaded otherwise CommandExecutionError.

    :rtype: bool

    .. code-block:: bash

        salt '*' crowdstrike.unload
    """
    return __salt__['crowdstrike.falconctl']('unload', timeout=30)


def status():
    """Determines whether or not if CrowdStrike Falcon is loaded.

    :return: A Boolean on whether or not crowdstrike is loaded.

    :rtype: bool

    .. code-block:: bash

        salt '*' crowdstrike.status
    """
    if not __salt__['crowdstrike.system_extension']():
        # if we should be using a kext, just check the kext as falconctl stats
        # can take a long time to run if falcon is already unloaded.
        if not __salt__['kext.running']('com.crowdstrike.sensor'):
            return False
    try:
        __salt__['crowdstrike.falconctl']('stats', timeout=5)
        return True
    except CommandExecutionError:
        return False


def license_(licenseid, load=True):
    """License crowdstrike falcon.

    :param str licenseid: license to use.

    :param bool load: If you want to load crowdstrike during licensing, defaults to True

    :return: A Boolean on whether or not crowdstrike was licensed.

    :rtype: bool

    .. code-block:: bash

        salt '*' crowdstrike.license
    """
    load = '' if load else '--noload'

    try:
        if 'Falcon.app' in __salt__['crowdstrike.falconctl_path']():
            __salt__['crowdstrike.falconctl']('license', licenseid, load, timeout=30)
        else:
            # there is no --noload option on v5 and you can't give it any
            # additional args or it will fail.
            __salt__['crowdstrike.falconctl']('license', licenseid, timeout=30)
        return True
    except CommandExecutionError:
        return False


def licensed():
    """Check if CrowdStrike is licensed of not.

    :return: A Boolean on whether or not crowdstrike is licensed.

    :rtype: bool

    .. code-block:: bash

        salt '*' crowdstrike.licensed
    """
    license_path = os.path.join(__salt__['crowdstrike.falcon_dir'](), 'License.bin')
    return True if os.path.exists(license_path) else False


def uninstall():
    """Uninstall CrowdStrike.

    :return: A Boolean on whether or not crowdstrike was uninstalled.

    :rtype: bool

    .. code-block:: bash

        salt '*' crowdstrike.uninstall
    """
    try:
        __salt__['crowdstrike.falconctl']('uninstall', timeout=30)
        return True
    except CommandExecutionError:
        return False


def get_groups():
    """Get the group tags that are set on the system.

    :return: A comma seperate string of all machine tags or an empty string if
    none are set.

    :rtype: str

    .. code-block:: bash

        salt '*' crowdstrike.get_groups
    """
    try:
        group_stdout = __salt__['crowdstrike.falconctl'](
            'grouping-tags', 'get', timeout=30, return_stdout=True)
        return group_stdout.split(': ')[1]
    except (CommandExecutionError, IndexError):
        return ' '


def set_groups(tags):
    """Set the group tags for Crowdstrike.

    :param str tags: Tag to set, for multiple use a comma seperated string.

    :return: Boolean of if set correctly or not.

    :rtype: Bool

    .. code-block:: bash

        salt '*' crowdstrike.set_groups
    """
    try:
        __salt__['crowdstrike.falconctl']('grouping-tags', 'set', tags, timeout=30)
        return True
    except CommandExecutionError:
        return False


def clear_groups():
    """Clear all group tags.

    :return: Boolean of if set correctly or not.

    :rtype: Bool

    .. code-block:: bash

        salt '*' crowdstrike.clear_groups
    """
    try:
        __salt__['crowdstrike.falconctl']('grouping-tags', 'clear', timeout=30)
        return True
    except CommandExecutionError:
        return False


def restart():
    """Restart Crowdstrike. Will unload and reload crowdstrike if it is
    already running. If it was previously not running it will load it
    then unload it.

    :return: True successfully restarted otherwise False.

    :rtype: Bool

    .. code-block:: bash

        salt '*' crowdstrike.restart
    """
    status = __salt__['crowdstrike.status']()
    if status:
        __salt__['crowdstrike.unload']()
    load = __salt__['crowdstrike.load']()
    # if we started unloaded, unload it again.
    if not status:
        return __salt__['crowdstrike.unload']()
    return load


def version():
    """Get the full falconctl version, if falcon isn't running it will
    return the Falcon.app version.

    :return: a version of the installed falcon.app

    :rtype: str

    .. code-block:: bash

        salt '*' crowdstrike.version
    """
    try:
        falcon_out = __salt__['crowdstrike.falconctl_plist']()
    except (CommandExecutionError):
        # if falconctl poops gets the app version
        return __salt__['crowdstrike.app_version']()
    falcon_data = plistlib.loads(falcon_out.encode())
    return falcon_data.get('agent_info', {}).get('version', 'unknown')


def app_version():
    """Get the app version of Falcon.app.

    :return: version of the app

    :rtype: str

    .. code-block:: bash

        salt '*' crowdstrike.app_version
    """
    falcon_app = pathlib.Path('/Applications/Falcon.app/')
    info_plist_path = falcon_app / 'Contents/Info.plist'
    try:
        info_plist = plistlib.loads(info_plist_path.read_bytes())
    except (FileNotFoundError):
        return 'unknown'
    return info_plist.get('CFBundleShortVersionString')


def agent_id():
    """Get the agent id of crowdstrike.

    :return: the agent id.

    :rtype: str

    .. code-block:: bash

        salt '*' crowdstrike.agent_id
    """
    try:
        falcon_out = __salt__['crowdstrike.falconctl_plist']()
    except (CommandExecutionError):
        return 'unknown'
    falcon_data = plistlib.loads(falcon_out.encode())
    return falcon_data.get('agent_info', {}).get('agentID')


def network_filter_status(app_id):
    """Get the status of the crowdstrike network filter.

    :param str tags: app_id to look for.
    :return: True if on and running, otherwise False.

    :rtype: bool

    .. code-block:: bash

        salt '*' crowdstrike.network_filter_status
    """
    ## borrowed with <3 from https://gist.github.com/erikng/407366fce4a3df6e1a5f8f44733f89ea
    enabled = False
    NetworkExtension = NSBundle.bundleWithPath_(
        '/System/Library/Frameworks/NetworkExtension.framework')
    NEConfigurationManager = NetworkExtension.classNamed_('NEConfigurationManager')
    manager = NEConfigurationManager.sharedManager()
    err = manager.reloadFromDisk()
    configs = manager.loadedConfigurations()

    if configs:
        for index, key in enumerate(configs):
            config = configs[key]
            if config.application() == app_id:
                enabled = config.contentFilter().isEnabled()

    return True if enabled else False


def enable_network_filter():
    """Attempts to enable the CrowdStrike Falcon network-filter.

    :return: A Boolean if successfully enabled otherwise CommandExecutionError.

    :rtype: bool

    .. code-block:: bash
        salt '*' crowdstrike.enable_network_filter
    """
    return __salt__['crowdstrike.falconctl']('enable-filter', timeout=30)


def disable_network_filter():
    """Attempts to disable the CrowdStrike Falcon network-filter.

    :return: A Boolean if successfully disabled otherwise CommandExecutionError.

    :rtype: bool

    .. code-block:: bash
        salt '*' crowdstrike.disable_network_filter
    """
    return __salt__['crowdstrike.falconctl']('disable-filter', timeout=30)
