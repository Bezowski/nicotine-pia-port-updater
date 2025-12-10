"""
PIA Port Updater - Nicotine+ Plugin
Automatically updates listening port from PIA VPN forwarded port file
"""

import os
import time
import threading
from pynicotine.pluginsystem import BasePlugin


class Plugin(BasePlugin):
    """
    Monitors /var/lib/pia/forwarded_port and updates Nicotine+ port automatically
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.settings = {
            'port_file': '/var/lib/pia/forwarded_port',
            'check_interval': 30
        }
        
        self.metasettings = {
            'port_file': {
                'description': 'Path to PIA forwarded port file',
                'type': 'str'
            },
            'check_interval': {
                'description': 'Check interval in seconds',
                'type': 'int',
                'minimum': 5
            }
        }
        
        self._last_port = None
        self._timer = None
        self.log("PIA Port Updater initialized")
        
        # Start the first check
        self.schedule_check()
    
    def schedule_check(self):
        """Schedule the next port check"""
        if self._timer is not None:
            self._timer.cancel()
        
        self._timer = threading.Timer(self.settings['check_interval'], self.check_and_update_port)
        self._timer.daemon = True
        self._timer.start()
    
    def check_and_update_port(self):
        """Check port file and update if changed"""
        try:
            port = self._read_port_file()
            self.log(f"Checked port file - Current: {port}, Last: {self._last_port}")
            
            if port and port != self._last_port:
                # Check if Nicotine+ already has this port configured
                current_port_range = self.config.sections["server"]["portrange"]
                if current_port_range == (port, port):
                    # Port is already correct, just update our tracking
                    self.log(f"Port {port} already configured, no reconnect needed")
                    self._last_port = port
                else:
                    # Port needs to be updated
                    self.log(f"New port detected: {port}")
                    self.update_port(port)
                    self._last_port = port
            elif port is None:
                self.log("Could not read port from file")
                
        except Exception as e:
            self.log(f"Error checking port: {e}")
        finally:
            # Schedule the next check
            self.schedule_check()
    
    def _read_port_file(self):
        """Read and validate port from file"""
        port_file = self.settings['port_file']
        
        if not os.path.exists(port_file):
            self.log(f"Port file does not exist: {port_file}")
            return None
        
        try:
            with open(port_file, 'r') as f:
                line = f.read().strip()
                
                if not line:
                    self.log("Port file is empty")
                    return None
                
                # File format is: "PORT EXPIRY_TIMESTAMP"
                # We only need the first value (the port)
                parts = line.split()
                if not parts:
                    self.log("Port file has no data")
                    return None
                
                port = int(parts[0])
                
                if 1024 <= port <= 65535:
                    # Check expiry timestamp if it exists
                    if len(parts) > 1:
                        expiry = int(parts[1])
                        if expiry < time.time():
                            self.log(f"Port {port} has expired")
                            return None
                    return port
                else:
                    self.log(f"Port {port} out of valid range (1024-65535)")
                    return None
                    
        except ValueError as e:
            self.log(f"Cannot parse port number: {e}")
            return None
        except IOError as e:
            self.log(f"Cannot read port file: {e}")
            return None
    
    def update_port(self, port):
        """Update Nicotine+ port configuration"""
        try:
            # Update port range in config
            self.config.sections["server"]["portrange"] = (port, port)
            
            # Reconnect to apply the new port
            self.core.reconnect()
            
            new_port_range = self.config.sections["server"]["portrange"]
            self.log(f"Port updated successfully to {new_port_range}")
            
        except Exception as e:
            self.log(f"Error updating port: {e}")
            self.log("Required Nicotine+ version is 3.3.7+ for reconnect method")
    
    def disable(self):
        """Stop the timer when plugin is disabled"""
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None
        self.log("PIA Port Updater disabled")
    
    def __del__(self):
        """Clean up when plugin is destroyed"""
        if self._timer is not None:
            self._timer.cancel()
