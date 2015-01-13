# Example installing or removing Adobe CC Extensions
---
com.github.salt-osx.extensionname:  # Extension name shown in extension manager
  ccextension.present:
    - source: /tmp/extension.zxp
    - enabled: True
#   - enabled: False

com.github.salt-osx.removed-extension:
  ccextension:
    - absent




