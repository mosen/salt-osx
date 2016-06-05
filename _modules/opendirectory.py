# -*- coding: utf-8 -*-
'''
Support for Directory Object Manipulation via the Open Directory Objective-C API

:maintainer:    Mosen <mosen@github.com>
:maturity:      new
:depends:       objc
:platform:      darwin
'''


import logging
from pprint import pprint

log = logging.getLogger(__name__)
has_imports = False

try:
    import objc
    from OpenDirectory import ODSession, ODQuery, ODNode, \
        kODRecordTypeUsers, kODAttributeTypeRecordName, kODMatchContains, kODAttributeTypeStandardOnly
    from Foundation import NSRunLoop, NSDefaultRunLoopMode, NSObject
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


def _get_node(path):
    '''
    Get a reference to an ODNode instance given a path string eg. /LDAPv3/127.0.0.1
    '''
    session = ODSession.defaultSession()
    node, err = ODNode.nodeWithSession_name_error_(session, path, None)

    if err:
        log.error(err)
        return None

    return node


def nodes():
    '''
    Get a list of registered nodes eg. /Local/Default

    CLI Example::

        salt '*' opendirectory.nodes
    '''
    session = ODSession.defaultSession()
    names, err = session.nodeNamesAndReturnError_(None)

    if err is not None:
        log.error(err)
        return None

    # The method returns with a tuple so it is converted to a list here.
    return list(names)


def search(path, searchValue):
    '''
    List records that match the given query.


    '''
    node = _get_node(path)

    if not node:
        log.error('Query not possible, cannot get reference to node at path: {}'.format(path))
        return None

    # @objc.callbackFor("CFOpenDirectory.ODQuerySetCallback")
    # def query_callback(query, value, context, error, info):
    #     log.warning('got callback')
    #     pass

    query, err = ODQuery.queryWithNode_forRecordTypes_attribute_matchType_queryValues_returnAttributes_maximumResults_error_(
        node,
        kODRecordTypeUsers,
        kODAttributeTypeRecordName,
        kODMatchContains,
        searchValue,
        kODAttributeTypeStandardOnly,
        0,
        None
    )

    if err:
        log.error('Failed to construct query: {}'.format(err))
        return None

    ODQueryDelegate = objc.protocolNamed('ODQueryDelegate')

    class QueryDelegate(NSObject, ODQueryDelegate):
        def query_foundResults_error_(self, inQuery, inResults, inError):
            log.error('FOUND RESULTS')

    qd = QueryDelegate()
    query.setDelegate_(qd)
    query.scheduleInRunLoop_forMode_(NSRunLoop.currentRunLoop(), NSDefaultRunLoopMode)



