# Example WiFi Payload
---
com.github.mosen.salt-osx.wifi.alacarte:
  profile.installed:
    - description: WiFi Payload
    - displayname: WiFi Payload
    - organization: Salt-OSX
    - content:
      - PayloadType: com.apple.wifi.managed
        HIDDEN_NETWORK: True
        AutoJoin: True
        ProxyType: None
        EncryptionType: WPA2
#        SetupModes:
#          -
#        AuthenticationMethod: ""
        Interface: BuiltInWireless
        SSID_STR: salt
        Password: saltstack
