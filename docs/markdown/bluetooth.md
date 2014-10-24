### bluetooth ###

Control the state of Bluetooth power and discoverability on the mac platform


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
    
