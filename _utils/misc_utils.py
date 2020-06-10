"""Helper functions for use by mac modules """


import logging
import os
from contextlib import contextmanager

import salt.utils.platform


log = logging.getLogger(__name__)


__virtualname__ = "misc_utils"


def __virtual__():
    """Load only on Mac OS"""
    if not salt.utils.platform.is_darwin():
        return (False, "The misc_utils utility could not be loaded: utility only works on MacOS.")

    return __virtualname__


@contextmanager
def user_context(uid):
    """Change execution UID while in this context

    May not work in all circumstances: probably not when run from
    a minion started by LaunchD. please test!

    Example:
    ```
    with user_context(__grains__['current_user_uid']):
        do_something()
    ```
    """
    original_uid = os.geteuid()
    log.debug("Setting EUID to %s", uid)
    try:
        os.seteuid(uid)
        yield
    finally:
        os.seteuid(original_uid)
