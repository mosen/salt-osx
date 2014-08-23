## salt-osx ##

Manage a mac fleet with SaltStack: Salt Modules/Grains/States for Mac OS X w/PyObjC. *Alpha Quality*

The motivation for this repository is to provide SaltStack modules that call into native Foundation/Cocoa API via PyObjC.
This would theoretically give you more control over configuration than scripting alone.

There are also some modules that use command line tools but expand on the support provided by salt.

## Installation ##

**VERY IMPORTANT:** You must disable multiprocessing on the Mac OS X minions for native modules to work. This is
because salt-minion threading does not work **at all** with CoreFoundation API. If you do not do this, the minion will 
crash without warning when trying to execute some modules. This is not the case with `salt-call` as it does not seem to 
use multiple threads.

You must edit your minion configuration file, usually `/etc/salt/minion` to include the following line:

    multiprocessing: False
    
This repository can then be added to your `file_roots` or whichever fileserver backend you happen to be using for your
master or masterless setup.

## Grains ##

- **filevault_enabled** FileVault state
- **java_vendor** JRE vendor (Apple or Oracle)
- **java_version** JRE version string

## States ##

### ard ###

Manage the options shown in the **Remote Management** preference pane.

### bluetooth ###

Control the state of Bluetooth power and discoverability on the mac platform

### plist ###

PropertyList management via YAML fragments.

## Execution Modules ##

### bluetooth ###

The **Bluetooth** module allows you to control the power and discoverability status of your macs bluetooth hardware.

*NOTE:* System preferences does not indicate whether the current device is discoverable.

The bluetooth module allows you to turn bluetooth on or off via

    bluetooth.on
    bluetooth.off
    
The "discoverable" status of bluetooth is controlled separately via

    bluetooth.discover
    
To allow discovery, or:

    bluetooth.nodiscover
    
To disallow discovery.


You can query the power status, and discoverability via these two execution modules:

    bluetooth.status
    bluetooth.discoverable
    
    
### desktop ###

The desktop module extends the salt core desktop module, providing you with settings and interactions for the current
users session, similar to those available via Apple Remote Desktop. Be aware that some commands will run immediately
and may interrupt what the user is currently doing.

You can get a list of every process in the current session using:

    desktop.processes
    
This will also list menu extras, and other items that may have been started via LaunchAgents.
    
You can query the wallpaper settings for all screens via:

    desktop.wallpaper
    
You can set the current wallpaper using the following execution module:

    desktop.set_wallpaper 0 '/Library/Desktop Pictures/Solid Colors/Solid Aqua Graphite.png'
    
The first parameter is the index of the screen, starting from 0. At the moment there is no way to designate the "main"
screen aka the screen that will contain the loginwindow. The second parameter of course is the full path to a local file
to use for the wallpaper.

At the moment custom colors are not supported, but if a wallpaper image is set, it always takes precedence over the solid
hex color.
    
## keychain ##

Not working at all.
ctypes and apple are working hard to break my brain.

## launchd ##

_TEMPORARILY BROKEN_ - Can't easily mix and match two API bridges, so this will have to go ctypes.

The launchd execution module allows you to query information about daemons/jobs currently running or loaded.
It does this using the built in `ServiceManagement` framework.

The following executions are available. Unless otherwise specified, every module runs in the 'system' context aka for
jobs that are loaded at the "root" level.

Get a list of loaded launchd jobs for the given context, one of 'user' or 'system':

    launchd.items system|user
    
Get detailed information about the launchd job definition, given a job label:

    launchd.info com.label system|user
    
Get the running process ID of a job:

    launchd.pidof com.label system|user
    
(TODO) `launchd.load` for loading a job definition from .plist, and `launchd.unload` for unloading via .plist

## login ##

The login module is designed to manage items related to the login process, and the customisation of the 
loginwindow.

### Login items (Shown in "System Preferences") ###

Get a list of login items (system wide) _Does not include LaunchAgents_:

    login.items system
    
Get a list of login items (current user) _Does not include LaunchAgents_:

    login.items user

### loginwindow customisation ###

Apple provides various customisations of the loginwindow via its preferences.
These commands give you shortcuts to modify the preferences, and take effect at next logout.
    
Get a list of user names hidden at the loginwindow:

    login.hidden_users
    
Get path to a picture, shown as the background of the loginwindow:

    login.picture
    
Set the loginwindow background picture:

    login.set_picture /path/to/background.jpg
    
Get text displayed at the footer of the loginwindow (if any):

    login.text
    
Or, set the footer text:

    login.set_text "Welcome to loginwindow"
    
Find out if auto-login is active, and which user it is set to:

    login.auto_login
    
Enable or disable auto-login for the specified username **NOTE: Not currently working, need to encode password hash**:

    login.set_auto_login true username  # To enable, or
    login.set_auto_login false          # to disable.
    
Get and set the display mode for the loginwindow, which is either a list of users with icons, or a username/password
input dialog.

    login.display_mode                  # Get mode list|inputs
    login.set_display_mode list|inputs  # Set mode 

Get and set the power/sleep button display

    login.display_power_buttons
    login.set_display_power_buttons true|false
    
(TODO) Display password hints y/n
(TODO) Display language input selection y/n

## plist ##

The plist module is designed to modify or create property list files anywhere on the filesystem.
At the moment it provides executions for querying, updating or removing individual key/values.
It also provides an API for other salt modules that rely on property list modification.

To read a single value:

    plist.read_key /path/to/file.plist <key>
    
To write a single value:
        
    plist.write_key /path/to/file.plist <key> <string|int|bool|float> 'the value'
    
To remove a key:

    plist.delete_key /path/to/file.plist <key>
    
## power ##

The power module controls the system power state, as well as forcing restarts and shutdowns.
Most of these take effect immediately, and will not allow the current session to save files or quit applications 
gracefully.

Sleep immediately:

    power.sleep
    
Shutdown is a basic wrapper around the shutdown command, default is 'now':

    power.shutdown now
    
Restart is a basic wrapper around `shutdown -r`, default is 'now':

    power.restart now
    
## TODO ##

General Roadmap Notes:

- SaltStack Shortcomings:
    + **services**: launchctl.py enumeration of standard directories could potentially be faster through other API
    methods. If i want to be really pedantic then `restart()` doesnt need the `-w` flag for overrides.
    + **user**: mac_user.py Badly needs ShadowHash implementation similar to macadmin in ruby.
    + **pkg**: brew.py/macports.py No implementation for `installer` tool? Steal another implementation just so that
    Salt could be used to bootstrap other package management solutions.
    + **netstat**: No netstat implementation for osx
    + **ps**: No ps implementation for osx
    
- Stuff that should be parity with macadmin:
    + computer/computer group records (DSLocal)
    + authorization db
    + everything and anything that relates to profile installation
    

- Need to support configuration profile management including generation and remote enrollment.