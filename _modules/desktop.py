"""
Interact with the current users login session

:maintainer:    Mosen <mosen@github.com>
:maturity:      new
:depends:       objc
:platform:      darwin
"""

import logging

log = logging.getLogger(__name__)

__virtualname__ = 'desktop'


def __virtual__():
    if __grains__.get('kernel') != 'Darwin':
        return False
    else:
        return __virtualname__


from Cocoa import NSWorkspace, \
    NSScreen, \
    NSWorkspaceDesktopImageScalingKey, \
    NSWorkspaceDesktopImageAllowClippingKey, \
    NSWorkspaceDesktopImageFillColorKey


def processes():
    '''
    Get a list of running processes in the user session

    TODO: optional get by bundle ID
    TODO: optional get hidden
    '''
    workSpace = NSWorkspace.sharedWorkspace()
    appList = workSpace.runningApplications()
    nameList = list()

    # Instances of NSRunningApplication
    for runningApp in appList:
        nameList.append(runningApp.localizedName())

    nameList.sort()
    return nameList


def restart():
    pass


def shutdown():
    pass


def logout():
    '''
    https://developer.apple.com/library/mac/qa/qa1134/_index.html
    https://developer.apple.com/library/mac/qa/qa1134/_index.html
    :return:
    '''


def sleep():
    pass


def open():
    '''
    Open application or file with NSWorkspace
    :return:
    '''
    pass


def _screenImageOptions(screen):
    '''
    Process an instance of NSScreen, returning its options as a hash
    '''
    workspace = NSWorkspace.sharedWorkspace()
    if (screen == NSScreen.mainScreen()):
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
    screens = NSScreen.screens()
    screen_list = [_screenImageOptions(screen) for screen in screens]
    return screen_list


def labels():
    '''
    Finder labels - NSWorkspace
    :return:
    '''

    # Launch Application
    # Open File
    # Eject device

    # Notify https://developer.apple.com/library/mac/documentation/NetworkingInternet/Conceptual/RemoteNotificationsPG/Introduction.html#//apple_ref/doc/uid/TP40008194-CH1-SW1