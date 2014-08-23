system:
  bluetooth:
    - managed
    - enabled: False
  ard:
    - managed
    - enabled: True
    - allow_all_users: True
    - all_users_privs:
      - text
      - copy
      - observe_hidden
    - enable_menu_extra: True
    - enable_dir_logins: True
    - directory_groups:
        - ard_users
        - ard_admins
        - ard_interact
    - enable_legacy_vnc: False
    - vnc_password: secret
    - allow_vnc_requests: True
    - allow_wbem_requests: True

admin:
  ard.privileges:
    - list:
      - all
      - observe_hidden


# Restrict AAM From Updating
/Library/Preferences/com.adobe.CSXSPreferences.plist:
  plist.managed_keys:
    - UpdatesAllowed: False

#/Library/Preferences/com.adobe.CSXSPreferences.plist:
#  plist.absent_keys:
#    - UpdatesAllowed: False
