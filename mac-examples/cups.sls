# Example adding a printer to a minion running CUPS
---
Example_Printer:
  printer:
    - present
    - description: 'SaltStack Example Printer'
    - uri: 'lpd://127.0.0.1/example'
    - location: 'Doesnt Exist'
    - model: 'drv:///sample.drv/laserjet.ppd'
    - options:
        PageSize: A4
        InputSlot: Tray2


#Example_Printer:
#  printer:
#    - absent
