# Example using a structure to manage key values in a propertylist file.
# The data types for the managed keys are guessed at this stage.
---
# Restrict AAM From Updating
/Library/Preferences/com.adobe.CSXSPreferences.plist:
  plist.managed_keys:
    - UpdatesAllowed: False

#/Library/Preferences/com.adobe.CSXSPreferences.plist:
#  plist.absent_keys:
#    - UpdatesAllowed: False