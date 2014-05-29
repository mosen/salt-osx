salt-osx
========

(Experimental) Salt modules for OSX w PyObjC.

The motivation for this repository is to provide SaltStack modules that call into native Foundation/Cocoa api via PyObjC.
This gives you control over a large number of aspects of OS X configuration, beyond what a simple command runner would do.

Because it's a playground at the moment, i wouldnt use it in any official capacity.

## bluetooth ##

The bluetooth module allows you to turn bluetooth on or off via

    bluetooth.on
    bluetooth.off

or query the status of bluetooth via:

    bluetooth.status
    
## desktop ##

The desktop module supersedes the salt core desktop module and provides the following executions:

You can list the applications/processes running in the current user session via:

    desktop.processes
    
You can query the wallpaper settings for all screens via:

    desktop.wallpaper
    
## keychain ##

Not working at all

## launchd ##

The launchd module uses the ServiceManagement framework to query launchd jobs.
The following executions are available, the default context is always 'system':

Get a list of loaded launchd jobs for the given context, one of 'user' or 'system':

    launchd.items system|user
    
Get detailed information about the launchd job definition, given a job label:

    launchd.info com.label system|user
    
Get the running process ID of a job:

    launchd.pidof com.label system|user

## login ##

The login module is designed to manage loginwindow functionality such as:
- LoginHook/LogoutHook
- Login items
- Loginwindow preferences

No functional executions yet.

## plist ##

The plist module is designed to modify or create property list files anywhere on the filesystem.
At the moment it provides executions for querying, updating or removing individual key/values:

To read a single value:

    plist.read_key /path/to/file.plist <key>
    
To write a single value:
        
    plist.write_key /path/to/file.plist <key> <string|int|bool|float> 'the value'
    
To remove a key:

    plist.delete_key /path/to/file.plist <key>
    
