{% from 'java/map.jinja' import java with context %}

# Updater options
/Library/Preferences/com.oracle.java.Java-Updater.plist:
  plist.managed_keys:
    - JavaAutoUpdateEnabled: {{ java.config.updates_enabled }}
#  plist.absent_keys:
#    - Nest:
#        NestedThing: 'NestedVal'
