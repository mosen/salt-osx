system:
  bluetooth:
    - managed
    - enabled: False
  ard:
    - managed
    - enabled: True
    - allow_all_users: True
    - all_users_privs:
      - all
      - observe_hidden
    - enable_menu_extra: False
    - enable_dir_logins: True
    - directory_groups:
        - ard_users
        - ard_admins
    - enable_legacy_vnc: True
    - vnc_password: secret
    - allow_vnc_requests: False
    - allow_wbem_requests: False

postgres:
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
