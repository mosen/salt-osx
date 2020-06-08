import logging

from LaunchServices import LSCopyDefaultHandlerForURLScheme, LSSetDefaultHandlerForURLScheme

import salt.utils.platform
# https://sheagcraig.github.io/configuring-and-reconfiguring-the-default-mail-reader-self-service-through-munki-and-a-tale-of-woe/


log = logging.getLogger(__name__)


__virtualname__ = "launchservices"


def __virtual__():
    if salt.utils.platform.is_darwin():
        return __virtualname__

    return (False, "module.launchservices is only available on macOS.")


def set_handler_for_scheme(scheme, bundle_id, user=None):
    """Set a user's default scheme handler to bundle_id.

    :param str scheme: URL scheme for which the handler is to be set.
    :param str bundle_id: App bundle id that is to be set as the handler.
    :param int: UID to set handler for. Defaults to current user.

    :return: Bool if successfully changed.

    :rtype: str

    CLI Example:

    .. code-block:: bash

        salt '*' handler.set mailto com.google.Chrome
        salt '*' handler.set mailto com.google.Chrome glorfindel
    """
    if user is None:
        user = __grains__['current_user_uid']
    with __utils__['misc_utils.user_context'](user):
        return LSSetDefaultHandlerForURLScheme(scheme, bundle_id) == 0


def get_handler_for_scheme(scheme, user=None):
    """Get a user's default scheme handler.

    :param str scheme: URL scheme for which the handler is to be retrieved.
    :param int: UID to get handler for. Defaults to current user.

    :return: The bundle ID for the default handler; may be empty.

    :rtype: str

    CLI Example:

    .. code-block:: bash

        salt '*' handler.get mailto
        salt '*' handler.get mailto gotti
    """
    if user is None:
        user = __grains__['current_user_uid']
    with __utils__['misc_utils.user_context'](user):
        # This function is deprecated, but strangely the setter is not.
        # Also, there's no recommendation for a replacement, and the
        # closest functionality available is with
        # LSCopyDefaultApplicationURLForURL, which doesn't return a
        # bundle identifier, but rather a URL to the application.
        return LSCopyDefaultHandlerForURLScheme(scheme) or ''

