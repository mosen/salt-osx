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
