system:
  bluetooth:
    - managed
    - enabled: False
  ard:
    - managed
    - enabled: True
    - allow_all_users: True
    - all_users_privs: "-1073741569"
    - enable_menu_extra: True
    - enable_dir_logins: True
    - directory_groups:
        - ard_users
        - ard_admins
    - enable_legacy_vnc: True
    - vnc_password: password
    - allow_vnc_requests: True
    - allow_wbem_requests: True
    - users:
      - joe: all
      - sally: observe


# Restrict AAM From Updating
/Library/Preferences/com.adobe.CSXSPreferences.plist:
  plist.managed_keys:
    - UpdatesAllowed: False

#/Library/Preferences/com.adobe.CSXSPreferences.plist:
#  plist.absent_keys:
#    - UpdatesAllowed: False
