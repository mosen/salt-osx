# Example creating a .mobileconfig profile
---
#com.salt-osx.activedirectory.alacarte:
#  profile:
#    - installed
#    - description: This description is shown underneath the display name
#    - displayname: Salt-OSX Example Profile
#    - organization: Salt-OSX Inc.
#    - removaldisallowed: False
#    - content:
#      - com.apple.DirectoryService.managed:
#            HostName: ad.saltosx.private
#            UserName: Administrator
#            Password: Pa$$w0rd
#            ADOrganizationalUnit: demo_ou
#            ADMountStyle: smb
#            ADDefaultUserShell: /bin/bash
#  #            ADMapUIDAttribute: ~
#  #            ADMapGIDAttribute: ~
#  #            ADMapGGIDAttribute: ~
#            ADNamespace: domain
#            ADDomainAdminGroupList:
#              - SALTOSX\UserA
#              - SALTOSX\UserB
#            ADPacketSign: allow
#            ADPacketEncrypt: allow
#            ADCreateMobileAccountAtLogin: False
#            ADWarnUserBeforeCreatingMA: True
#            ADForceHomeLocal: True
#            ADUseWindowsUNCPath: True
#            ADAllowMultiDomainAuth: True
#            ADTrustChangePassIntervalDays: 0

com.salt-osx.vpn.alacarte:
  profile.installed:
    - description: An example VPN Payload
    - displayname: salt-osx example VPN payload
    - organization: salt-osx inc.
    - removaldisallowed: False
    - content:
      - com.apple.vpn.managed:
          UserDefinedName: Salt Test VPN
          OverridePrimary: True
          VPNType: PPTP
          OnDemandEnabled: 0
          PPP:
            CommRemoteAddress: vpn.salt.private
            AuthName: salt
            AuthPassword: salt
            TokenCard: False
            CCPEnabled: True
            CCPMPPE128Enabled: True
            CCPMPPE40Enabled: True


