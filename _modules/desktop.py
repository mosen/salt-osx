"""
Interact with the current user's login session.

:maintainer:    Mosen <mosen@github.com>
:maturity:      new
:depends:       objc,Foundation,Cocoa
:platform:      darwin
"""

import logging

log = logging.getLogger(__name__)

HAS_LIBS = False
try:
    from Cocoa import NSWorkspace, \
        NSScreen, \
        NSWorkspaceDesktopImageScalingKey, \
        NSWorkspaceDesktopImageAllowClippingKey, \
        NSWorkspaceDesktopImageFillColorKey

    from Foundation import NSURL, \
        NSDictionary

    HAS_LIBS = True
except ImportError:
    log.debug('Execution module not suitable because one or more imports failed.')

__virtualname__ = 'desktop'


def __virtual__():
    '''
    Only load if the platform is correct and we can use PyObjC libs
    '''
    if __grains__.get('kernel') != 'Darwin':
        return False

    if not HAS_LIBS:
        return False

    return __virtualname__

def open_url(url):
    '''
    Open a URL in the current users session.
    This works with anything that command-k would accept, such as:
    afp, smb, vnc, http

    CLI Example::

        salt '*' desktop.open_url 'afp://server.local'
    '''
    workSpace = NSWorkspace.sharedWorkspace()
    url = NSURL.URLWithString_(url)
    if url is None:
        log.error('Invalid URL given: %s' % url)
        return False

    status = workSpace.openURL_(url)
    return status


def open_file(path):
    '''
    Open a file in the current users session (using the default application).
    This requires the full path to the file.

    CLI Example::

        salt '*' desktop.open_file '/Users/Shared'
    '''
    workSpace = NSWorkspace.sharedWorkspace()
    status = workSpace.openFile_(path)
    return status





def _screenImageOptions(screen):
    '''
    Process an instance of NSScreen, returning its options as a hash
    '''
    workspace = NSWorkspace.sharedWorkspace()
    if screen == NSScreen.mainScreen():
        is_main = True
    else:
        is_main = False

    screen_options = workspace.desktopImageOptionsForScreen_(screen)
    scaling_factor = screen_options.objectForKey_(NSWorkspaceDesktopImageScalingKey)  # NSImageScaling : NSNumber
    allow_clipping = screen_options.objectForKey_(NSWorkspaceDesktopImageAllowClippingKey)  # NSNumber
    fill_color = screen_options.objectForKey_(NSWorkspaceDesktopImageFillColorKey)  # NSColor
    image_url = workspace.desktopImageURLForScreen_(screen).absoluteString()  # NSURL
    options_dict = {'main': is_main, 'scaling_factor': scaling_factor, 'image_url': image_url,
                    'allow_clipping': allow_clipping}
    if fill_color:
        options_dict['fill_color'] = {'r': fill_color.redComponent(), 'g': fill_color.greenComponent(),
                                      'b': fill_color.blueComponent()}

    return options_dict


# https://developer.apple.com/library/mac/samplecode/DesktopImage/Introduction/Intro.html
def wallpaper():
    '''
    Get desktop wallpaper for every screen, including scaling options.

    CLI Example:

    .. code-block:: bash

        salt '*' desktop.wallpaper
    '''
    log.info('Enumerating settings for each screen')
    screens = NSScreen.screens()
    log.info('Getting settings for %d screen(s)', len(screens))
    screen_list = [_screenImageOptions(screen) for screen in screens]
    from pprint import pprint
    pprint(screen_list)

    return screen_list


# No scaling options yet (or main screen detection)
def set_wallpaper(screen_index, path):
    '''
    Set desktop wallpaper for screen at index

    CLI Example:

    .. code-block:: bash

        salt '*' desktop.set_wallpaper 0 '/Library/Desktop Pictures/Solid Colors/Solid Aqua Graphite.png'
    '''
    workspace = NSWorkspace.sharedWorkspace()
    screens = NSScreen.screens()
    screen = screens[screen_index]
    file_url = NSURL.fileURLWithPath_isDirectory_(path, False)
    options = {}

    (status, error) = workspace.setDesktopImageURL_forScreen_options_error_(file_url, screen, options, None)
    return status

