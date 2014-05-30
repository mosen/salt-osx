"""
Query information about the Finder configuration

:maintainer:    Mosen <mosen@github.com>
:maturity:      new
:depends:       objc
:platform:      darwin
"""

import logging

log = logging.getLogger(__name__)  # Start logging

HAS_LIBS = False
try:
    from LaunchServices import LSSharedFileListCreate, \
        kLSSharedFileListFavoriteItems, \
        kLSSharedFileListFavoriteVolumes, \
        kLSSharedFileListVolumesComputerVisible, \
        kLSSharedFileListVolumesNetworkVisible, \
        LSSharedFileListRef, \
        LSSharedFileListCopySnapshot, \
        LSSharedFileListItemCopyDisplayName

    from Cocoa import NSWorkspace

    HAS_LIBS = True
except ImportError:
    log.debug('Execution module not suitable because one or more imports failed.')

__virtualname__ = 'finder'


def __virtual__():
    '''
    Only load if the platform is correct and we can use PyObjC libs
    '''
    if __grains__.get('kernel') != 'Darwin':
        return False

    if not HAS_LIBS:
        return False

    return __virtualname__


def favorites():
    '''
    Get items listed as Finder favorites, this normally appears on the sidebar.
    '''
    lst = LSSharedFileListCreate(None, kLSSharedFileListFavoriteItems, None)
    snapshot, seed = LSSharedFileListCopySnapshot(lst, None)  # snapshot is CFArray

    return [LSSharedFileListItemCopyDisplayName(item) for item in snapshot]


def devices():
    '''
    Get items listed as Finder devices, this normally appears on the sidebar.
    '''
    lst = LSSharedFileListCreate(None, kLSSharedFileListFavoriteVolumes, None)
    snapshot, seed = LSSharedFileListCopySnapshot(lst, None)  # snapshot is CFArray

    return [LSSharedFileListItemCopyDisplayName(item) for item in snapshot]


def labels():
    '''
    Get Finder labels (Not including user defined tags, they are identified by NSURLTagNamesKey)
    '''
    workSpace = NSWorkspace.sharedWorkspace()
    return workSpace.fileLabels()
