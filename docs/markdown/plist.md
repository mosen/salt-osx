### plist ###

PropertyList management via YAML fragments.

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
    
