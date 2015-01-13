# Example WiFi Payload
---
com.github.mosen.salt-osx.wifi.alacarte:
  profile.installed:
    - description: WiFi Payload
    - displayname: WiFi Payload
    - organization: Salt-OSX
    - content:
      - PayloadType: com.apple.wifi.managed
        SSID_STR: salt
        HIDDEN_NETWORK: True
        AutoJoin: True
        ProxyType: None
        EncryptionType: WPA
        #AuthenticationMethod: ""
        Interface: BuiltInWireless
        # WPA Encryption Fields
        Password: saltstack
