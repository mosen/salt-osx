# Example adding a printer to a minion running CUPS
---
Example_Printer:
  printer:
    - present
    - description: 'SaltStack Example Printer'
    - uri: 'lpd://127.0.0.1/example'
    - location: 'Doesnt Exist'
    - model: 'drv:///sample.drv/generic.ppd'

#Example_Printer:
#  printer:
#    - absent
