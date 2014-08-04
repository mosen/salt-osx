system:
  bluetooth:
    - managed
    - enabled: False
  munki:
    - client
    - identifier: sales

# Restrict AAM From Updating
/Library/Preferences/com.adobe.CSXSPreferences.plist:
  plist.managed_keys:
    - UpdatesAllowed: False
