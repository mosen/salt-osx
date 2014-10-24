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
    
