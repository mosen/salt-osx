# Example of power management/energy saver settings.
# These parameters are exactly the same as the pmset(1) command line tool on mac os x
---
ac:
  power:
    - settings
    - displaysleep: 0  # Number of minutes to sleep display, zero always means never sleep
    - disksleep: 0  # Disk spin down
    - sleep: 0  # System sleep
    - womp: True  # Wake on ethernet magic packet
    - ring: False  # Wake on modem ring
    - autorestart: True  # Auto restart on power loss
    - lidwake: True  # Wake when lid is opened
    - acwake: False  # Wake when power source is changed
    - lessbright: False  # Turn down brightness when switching to this power source
    - halfdim: False  # Display sleep uses half brightness
    - sms: True  # Use sudden motion sensor to park disk heads
    - ttyskeepawake: True  # Prevent system sleep when tty (remote login) is active.
    - destroyfvkeyonstandby: False  # Destroy FileVault key on standby, user will require FV password coming out of sleep.
    - autopoweroff: False  # Hibernate after sleeping for a certain amount of time.
    - autopoweroffdelay: 10  # Delay after sleeping to hibernate, in minutes

# The name may be "ac", "battery", or "ups"
battery:
  power:
    - settings
    # ...

