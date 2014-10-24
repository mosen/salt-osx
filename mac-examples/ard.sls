# Example using all ard state options to manage the 'Remote Management' service on OSX
# The second example shows a local admin user being granted privileges for the 'Remote Management' service.
---
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