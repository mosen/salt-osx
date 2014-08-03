"""
Query information about the Finder configuration

:maintainer:    Mosen <mosen@github.com>
:maturity:      new
:depends:       objc,LaunchServices,Cocoa.NSWorkspace
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


def select(path, finder_path=""):
    '''
    Reveal the finder and select the file system object at the given path.
    If the second parameter is specified, a new finder window will be opened at that path.
    Otherwise, an existing finder window will be used.

    CLI Example::

        salt '*' finder.select '/Users/Shared' '/Users'
    '''
    workSpace = NSWorkspace.sharedWorkspace()
    status = workSpace.selectFile_inFileViewerRootedAtPath_(path, finder_path)
    return status


def search(query):
    '''
    Reveal the finder and search in Spotlight, with the given query.

    CLI Example::

        salt '*' finder.search 'Documents'
    '''
    workSpace = NSWorkspace.sharedWorkspace()
    status = workSpace.showSearchResultsForQueryString_(query)
    return status


def favorites():
    '''
    Get items listed as Finder favorites, this normally appears on the sidebar.
    Because the minion runs as root, this function returns sidebar items for root which is not terribly useful.

    CLI Example::

        salt '*' finder.favorites
    '''
    lst = LSSharedFileListCreate(None, kLSSharedFileListFavoriteItems, None)
    snapshot, seed = LSSharedFileListCopySnapshot(lst, None)  # snapshot is CFArray

    return [LSSharedFileListItemCopyDisplayName(item) for item in snapshot]


def devices():
    '''
    Get items listed as Finder devices, this normally appears on the sidebar.
    This would normally return mounted devices for root, but since mounts are usually system wide, this will be ok.

    CLI Example::

        salt '*' finder.devices
    '''
    lst = LSSharedFileListCreate(None, kLSSharedFileListFavoriteVolumes, None)
    snapshot, seed = LSSharedFileListCopySnapshot(lst, None)  # snapshot is CFArray

    return [LSSharedFileListItemCopyDisplayName(item) for item in snapshot]


def labels():
    '''
    Get Finder labels (Not including user defined tags, they are identified by NSURLTagNamesKey)
    '''
    workSpace = NSWorkspace.sharedWorkspace()
    return list(workSpace.fileLabels())
