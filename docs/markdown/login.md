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
