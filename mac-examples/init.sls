system:
  bluetooth:
    - managed
    - enabled: False


# Restrict AAM From Updating
/Library/Preferences/com.adobe.CSXSPreferences.plist:
  plist.managed_keys:
    - UpdatesAllowed: False

#/Library/Preferences/com.adobe.CSXSPreferences.plist:
#  plist.absent_keys:
#    - UpdatesAllowed: False
