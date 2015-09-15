# -*- coding: utf-8 -*-
'''
Manage running applications.

Similar to `ps`, you can treat running applications as unix processes.

On OS X, there is a higher level Cocoa functionality (see NSApplication) which responds to events sent through the
notification center. This module operates at that level.

:maintainer:    Mosen <mosen@github.com>
:maturity:      beta
:depends:       objc
:platform:      darwin
'''
import logging
import salt.utils

log = logging.getLogger(__name__)

__virtualname__ = 'app'

HAS_LIBS = False
try:
    from Cocoa import NSWorkspace
    HAS_LIBS = True
except ImportError:
    log.debug('Execution module not suitable because one or more imports failed.')

def __virtual__():
    '''
    Only load module if we are running on OS X.
    '''
    return __virtualname__ if HAS_LIBS else False


def quit(appname, blocking=False):
    '''
    Ask an application to quit.
    Does not guarantee that the application will quit without user interaction.
    Does not block until the application quits.

    :param application:
    :return:
    '''
    workSpace = NSWorkspace.sharedWorkspace()
    applications = workSpace.runningApplications()

    for app in applications:
        if app.localizedName() == appname:
            acknowledged = app.terminate()
            return acknowledged

    return None


def force_quit(appname, blocking=False):
    '''
    Force an application to quit aka `Force Quit`.
    Does not block until the application quits.

    :param application:
    :return:
    '''
    workSpace = NSWorkspace.sharedWorkspace()
    applications = workSpace.runningApplications()

    for app in applications:
        if app.localizedName() == appname:
            acknowledged = app.forceTerminate()
            return acknowledged

    return None

def launch(application):
    '''
    Open an Application by name.
    This does not need to be the full path to the application, and does not need to have an .app extension.

    CLI Example::

        salt '*' desktop.launch 'TextEdit'
    '''
    workSpace = NSWorkspace.sharedWorkspace()
    status = workSpace.launchApplication_(application)
    return status


def processes():
    '''
    Get a list of running processes in the user session

    TODO: optional get by bundle ID
    TODO: optional get hidden
    '''
    workSpace = NSWorkspace.sharedWorkspace()
    appList = workSpace.runningApplications()

    names = [app.localizedName() for app in appList]

    names.sort()
    return names


def frontmost():
    '''
    Get the name of the frontmost application
    '''
    workSpace = NSWorkspace.sharedWorkspace()
    app = workSpace.frontmostApplication()

    return app.localizedName()

