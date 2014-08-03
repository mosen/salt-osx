include:
  - java.config

system:
  bluetooth:
    - managed
    - enabled: False
  munki:
    - client
    - identifier: sales
#    - repo_url: 'http://munki/repo'


# Restrict AAM From Updating
/Library/Preferences/com.adobe.CSXSPreferences.plist:
  plist.managed_keys:
    - UpdatesAllowed: False


#salt:
#  user.present:
#    - fullname: SaltStack
