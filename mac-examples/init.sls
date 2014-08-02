system:
  bluetooth:
    - managed
    - enabled: False
  munki:
    - client
    - identifier: sales
#    - repo_url: 'http://munki/repo'

# Disable Oracle JRE Updates
/Library/Preferences/com.oracle.java.Java-Updater.plist:
  plist.managed_keys:
    - JavaAutoUpdateEnabled: True


