"""State for managing macOS LaunchServices"""


import logging

import salt.utils.platform


log = logging.getLogger(__name__)


__virtualname__ = 'launchservices'


def __virtual__():
    """Only make available for the Mac platform."""
    if salt.utils.platform.is_darwin():
        return __virtualname__
    else:
        return False, 'state.launchservices only available on macOS'


def managed_handler_for_scheme(name, bundle_id, user=None):
    """
    Ensure a handler is specified for a URL scheme.

    :param str scheme: URL scheme for which the handler is to be set.
    :param str bundle_id: App bundle id that is to be set as the handler.
    :param int: UID to set handler for. Defaults to current user.

    .. code-block:: yaml
        # Only do it once per user so they can change if desired.
        Ensure browser will handle mailtos:
          prefs.write:
            - name: com.tacotruck.cpe.mailto_handler
            - value: {{ grains['current_user'] }}
            - domain: com.tacotruck.cpe.tags
            - user: any
            - host: current
          launchservices.managed_handler_for_scheme:
            - name: mailto
            - bundle_id: com.google.Chrome
            - user: {{ grains['current_user_uid'] }}
            - onchanges:
              - prefs: com.tacotruck.cpe.mailto_handler
    """
    ret = {'name': name,
           'changes': {},
           'result': False,
           'comment': ''}

    result = __salt__['launchservices.get_handler_for_scheme'](name, user)

    if result == bundle_id:
        ret['result'] = True
        ret['comment'] = 'Handler already set.'
        return ret

    if __opts__['test']:
        ret['result'] = None
        ret['comment'] = 'Handler {} would be set for {}'.format(bundle_id, name)
        return ret

    __salt__['launchservices.set_handler_for_scheme'](name, bundle_id, user)
    ret['result'] = __salt__['launchservices.get_handler_for_scheme'](name, user)

    if not ret['result']:
        ret['comment'] = 'Handler {} was not set for {}'.format(bundle_id, name)
    else:
        ret['comment'] = 'Handler {} was set for {}.'.format(bundle_id, name)
        ret['changes'].update({name: {'old': result, 'new': name}})
    return ret

