"""
State to manage various pieces of crowdstrike. Some brief examples below.

The is capable of handling both major versions of crowdstrike 5 and 6.
If first looks for version 6. If found it will manage that version if not it
will look for version 5.

Some of these states will most likely not work if you use tamper protection. Adding
support to pass the key in should be trivial.

# ensure the crowdstrike is running and has some sensor tags set.
# NOTE: the license_key will show up in the process list.
.. code-block:: yaml
    apps_crowdstrike_ensure_falcon_running:
        crowdstrike.running:
            - name: com.crowdstrike.sensor
            - license_key: 1BB86IW04SWF9BG71Z8OU3G227MJHRR-71

    apps_crowdstrike_set_group_tags:
        crowdstrike.grouping_tags:
            - name: CrowdStrike Tags
            - tags:
                - eng
                - shard_10

You can also set tags to a machine you don't want running. The state will automatically
enable the sensor to give it time to send the Tags to the console then finish disabling it.

.. code-block:: yaml
    apps_crowdstrike_ensure_falcon_dead:
        crowdstrike.dead:
            - name: com.crowdstrike.sensor

    apps_crowdstrike_set_disabled_tag:
        crowdstrike.grouping_tags:
            - name: Disabled CrowdStrike Tag
            - tags:
                - disabled
"""
import os

import salt.utils.platform

__virtualname__ = 'crowdstrike'


def __virtual__():
    """Only macOS for now.

    TODO: add windows/linux support.
    """
    if not salt.utils.platform.is_darwin():
        return (False, 'Crowdstrike state only available on macOS.')

    if (not os.path.exists('/Library/CS/falconctl') and
            not os.path.exists('/Applications/Falcon.app/Contents/Resources/falconctl')):
        return (False, 'Failed to load the crowdstrike module. falconctl not found')

    return __virtualname__


def dead(name):
    """Ensure that crowdstrike is not loaded/running."""
    ret = {'name': name, 'result': True, 'changes': {}, 'comment': ''}

    # check if crowdstrike is running properly.
    falcon_status = __salt__['crowdstrike.status']()

    # if it's not running then we good.
    if not falcon_status:
        ret['comment'] = 'Crowdstrike is dead.'
        return ret

    if __opts__['test']:
        ret['result'] = None
        ret['comment'] = 'Crowdstrike would be unloaded.'
        return ret

    unload_crowdstrike = __salt__['crowdstrike.unload']()

    if not unload_crowdstrike:
        ret['result'] = False
        ret['comment'] = 'Failed to unload crowdstrike.'
        return ret

    ret['comment'] = 'Successfully unloaded crowdstrike.'
    ret['changes'].update({name: {'old': 'Running', 'new': 'Dead'}})
    return ret


def running(name, license_key=None):
    """Ensure that Crowdstrike is loaded/running.

    name:
        any name will do, just needed for salts state system.

    license:
        if specified, crowdstrike will be licensed with the key given here.
    """
    ret = {'name': name, 'result': True, 'changes': {}, 'comment': ''}
    license_ret = {'name': name, 'result': True, 'changes': {}, 'comment': ''}

    if license_key:
        license_ret = __states__['crowdstrike.licensed'](license_key)

    # check to see if our crowdstrike is running.
    crowdstrike_running = __salt__['crowdstrike.status']()

    if crowdstrike_running:
        ret['comment'] = 'CrowdStrike is running.'
        if license_ret['comment']:
            ret['comment'] = f"CrowdStrike is running and {license_ret['comment']}"
        ret['changes'] = license_ret['changes']
        return ret

    if __opts__['test']:
        ret['result'] = None
        ret['comment'] = 'CrowdStrike will be loaded.'
        return ret

    load_crowdstrike = __salt__['crowdstrike.load']()

    if not load_crowdstrike:
        ret['result'] = False
        ret['comment'] = 'Failed to start CrowdStrike.'
        return ret

    ret['comment'] = 'Successfully started CrowdStrike.'
    if license_ret['comment']:
        ret['comment'] = f"Successfully started CrowdStrike and {license_ret['comment']}"

    ret['changes'].update({name: {'old': 'Dead', 'new': 'Running'}})
    if license_ret['changes']:
        ret['changes'].update(license_ret['changes'])

    return ret


def licensed(name):
    """Ensure that Crowdstrike is licensed.

    .. note::
        This state will ONLY license crowdstrike if it isn't licensed. This
        state should NOT be used to change the license.

    name:
        the customer id to license the machine with.
    """
    ret = {'name': name, 'result': True, 'changes': {}, 'comment': ''}

    # check if clownstrike is licensed.
    falcon_license_status = __salt__['crowdstrike.licensed']()

    # if it's licensed then we are good.
    if falcon_license_status:
        ret['comment'] = 'CrowdStrike is already licensed.'
        return ret

    if __opts__['test']:
        ret['result'] = None
        ret['comment'] = 'CrowdStrike would be licensed.'
        return ret

    license_crowdstrike = __salt__['crowdstrike.license'](name, load=False)

    if not license_crowdstrike:
        ret['result'] = False
        ret['comment'] = 'Failed to license CrowdStrike.'
        return ret

    ret['comment'] = 'Successfully licensed CrowdStrike.'
    ret['changes'].update({name: {'old': 'un-licensed', 'new': 'Licensed'}})
    return ret


def grouping_tags(name, tags=None):
    """Ensure that group tags are set.

    name: unused.
    tags: a list of tags you would like to set.
    """
    ret = {'name': name, 'result': True, 'changes': {}, 'comment': ''}

    if tags is None:
        ret['result'] = False
        ret['comment'] = 'Crowdstrike grouping_tags requires a list of tags.'
        return ret

    # sort tags into comma separated string as thats what the CLI takes.
    tag_str = ','.join(tags)

    # check the crowdstrike groups.
    groups = __salt__['crowdstrike.get_groups']()

    if groups == tag_str:
        ret['comment'] = 'Crowdstrike grouping tags are set correctly.'
        return ret

    if __opts__['test']:
        ret['result'] = None
        ret['comment'] = f'CrowdStrike grouping tags would be set to [{tag_str}].'
        return ret

    set_groups = __salt__['crowdstrike.set_groups'](tag_str)

    if not set_groups:
        ret['result'] = False
        ret['comment'] = 'Failed to set CrowdStrike grouping tags.'
        return ret

    # restart CrowdStrike so the new tags will get sent to the server.
    __salt__['crowdstrike.restart']()

    ret['comment'] = 'Successfully set CrowdStrike grouping tags.'
    ret['changes'].update({'grouping_tags': {'old': groups, 'new': tag_str}})
    return ret
