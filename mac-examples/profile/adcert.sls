# Example creating an AD certificate request payload
---
com.github.mosen.salt-osx.alacarte:
  profile.installed:
    - description: AD Certificate Request Payload
    - displayname: AD Certificate Request Payload
    - organization: Salt-OSX
    - content:
      - PayloadType: com.apple.adcertificate.managed
        CertTemplate: Machine
        CertificateAcquisitionMechanism: RPC
        PromptForCredentials: NO  # Only applies to User type template
        Description: Certificate Request Payload
        CertServer: ca.salt.private
        CertificateAuthority: SALT-CA  # Must be the short common name in certificate