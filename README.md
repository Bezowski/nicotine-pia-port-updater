# PIA Port Updater for Nicotine+

Automatically updates Nicotine+ listening port from PIA VPN forwarded port.

## Features

- Monitors `/var/lib/pia/forwarded_port` for port changes
- Automatically updates Nicotine+ port configuration
- Smart file monitoring - only reads when file is modified (low overhead)
- Checks port expiry to avoid using expired ports
- Configurable check interval (default: 30 seconds)
- Smart reconnection - only reconnects when port actually changes
- Optional auto-reconnect - can be disabled if you prefer manual reconnection
- Configurable logging levels (minimal/normal/verbose)
- Settings changes apply immediately without plugin restart

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

- **port_file**: Path to PIA forwarded port file (default: `/var/lib/pia/forwarded_port`)
- **check_interval**: How often to check for port changes in seconds (default: 30)
  - Note: Only checks file modification time, very low overhead
  - Changes apply immediately without plugin restart
- **auto_reconnect**: Automatically reconnect when port changes (default: enabled)
  - Disable if you prefer to manually reconnect or want to update port without disruption
- **log_level**: Logging verbosity (default: normal)
  - **minimal**: Only errors and critical updates
  - **normal**: Port changes, initialization, and important events
  - **verbose**: Every check and scheduling event (useful for debugging)

## How It Works

1. The plugin checks the modification time of the port file at regular intervals
2. If the file hasn't changed, it skips reading (very efficient)
3. When the file is modified, it reads and validates the new port
4. If the port has changed and hasn't expired, it updates Nicotine+ configuration
5. Optionally reconnects to apply the new port immediately

## Requirements

- Nicotine+ 3.3.7+
- PIA VPN with port forwarding enabled
- Port forwarding script from: https://github.com/pia-foss/manual-connections

## Troubleshooting

### Plugin not detecting port changes
- Verify the port file exists and is readable: `cat /var/lib/pia/forwarded_port`
- Set log_level to "verbose" to see detailed check information
- Check that check_interval isn't too long

### Port updates but no reconnection
- Check that auto_reconnect is enabled in plugin settings
- Verify Nicotine+ version is 3.3.7 or higher

### Too many log messages
- Set log_level to "minimal" or "normal"

## Credits

Plugin created by bez with assistance from Claude (Anthropic)

## License

MIT License - see LICENSE file for details
