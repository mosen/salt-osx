# -*- coding: utf-8 -*-
'''
Support for Directory Object Manipulation via the Open Directory Objective-C API

'''


import logging
from pprint import pprint

log = logging.getLogger(__name__)
has_imports = False

try:
    from OpenDirectory import ODSession, ODQuery
    has_imports = True
except ImportError:
    pass


def __virtual__():
    '''
    Module only loads on Darwin
    '''
    if not has_imports:
        return False, 'Open Directory only available on Darwin'
    else:
        return True


def _get_session():
    return ODSession.defaultSession()


def nodes():
    '''
    Get a list of registered nodes eg. /Local/Default
    '''
    session = ODSession.defaultSession()
    names, err = session.nodeNamesAndReturnError_(None)

    if err is not None:
        log.error(err)
        return None

    # The method returns with a tuple so it is converted to a list here.
    return list(names)


