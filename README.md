# PIA Port Updater for Nicotine+

Automatically updates Nicotine+ listening port from PIA VPN forwarded port.

## Features

- Monitors `/var/lib/pia/forwarded_port` for port changes
- Automatically updates Nicotine+ port configuration
- Checks port expiry to avoid using expired ports
- Configurable check interval (default: 30 seconds)
- Smart reconnection - only reconnects when port actually changes

## Installation

1. Copy the `pia-port-set` folder to your Nicotine+ plugins directory:
```bash
   cp -r pia-port-set ~/.local/share/nicotine/plugins/
```

2. Ensure the PIA port file is readable:
```bash
   sudo chmod 644 /var/lib/pia/forwarded_port
   sudo chmod 755 /var/lib/pia
```

3. Restart Nicotine+ and enable the plugin in Preferences → Plugins

## Configuration

Configure in Nicotine+ Preferences → Plugins → PIA Port Updater:
- `port_file`: Path to PIA forwarded port file (default: `/var/lib/pia/forwarded_port`)
- `check_interval`: How often to check for port changes in seconds (default: 30)

## Requirements

- Nicotine+ 3.3.7+
- PIA VPN with port forwarding enabled
- Port forwarding script from: https://github.com/pia-foss/manual-connections

## Credits

Plugin created with assistance from Claude (Anthropic)
