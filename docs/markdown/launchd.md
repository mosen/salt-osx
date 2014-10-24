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

