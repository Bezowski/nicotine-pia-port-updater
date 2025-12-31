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
            'check_interval': 30,
            'auto_reconnect': True,
            'log_level': 'normal'  # 'minimal', 'normal', 'verbose'
        }
        
        self.metasettings = {
            'port_file': {
                'description': 'Path to PIA forwarded port file',
                'type': 'str'
            },
            'check_interval': {
                'description': 'Check interval in seconds (only checks mtime, very low overhead)',
                'type': 'int',
                'minimum': 5
            },
            'auto_reconnect': {
                'description': 'Automatically reconnect when port changes',
                'type': 'bool'
            },
            'log_level': {
                'description': 'Logging verbosity (minimal/normal/verbose)',
                'type': 'dropdown',
                'options': ['minimal', 'normal', 'verbose']
            }
        }
        
        self._last_port = None
        self._last_mtime = None
        self._timer = None
        self._running = False
        self._lock = threading.Lock()
        self._check_count = 0
        
        self._log("PIA Port Updater initialized", level='normal')
        
        # Start the first check
        self._running = True
        self.schedule_check()
    
    def _log(self, message, level='normal'):
        """Internal logging method with configurable verbosity"""
        log_levels = {'minimal': 0, 'normal': 1, 'verbose': 2}
        current_level = log_levels.get(self.settings.get('log_level', 'normal'), 1)
        message_level = log_levels.get(level, 1)
        
        if message_level <= current_level:
            self.log(message)
    
    def schedule_check(self):
        """Schedule the next port check"""
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None
            
            if not self._running:
                self._log("Not scheduling check - plugin not running", level='verbose')
                return
            
            interval = self.settings.get('check_interval', 30)
            self._log(f"Scheduling check #{self._check_count + 1} in {interval} seconds", level='verbose')
            
            self._timer = threading.Timer(
                interval, 
                self.check_and_update_port
            )
            self._timer.daemon = True
            self._timer.start()
    
    def check_and_update_port(self):
        """Check port file and update if changed"""
        self._check_count += 1
        self._log(f"Running check #{self._check_count}", level='verbose')
        
        if not self._running:
            self._log("Check aborted - plugin not running", level='verbose')
            return
        
        try:
            # Check if file has been modified before reading
            port_file = self.settings['port_file']
            
            if not os.path.exists(port_file):
                self._log(f"Port file does not exist: {port_file}", level='normal')
                return
            
            current_mtime = os.path.getmtime(port_file)
            
            # Only read file if it has been modified
            if self._last_mtime is not None and current_mtime == self._last_mtime:
                self._log("Port file unchanged, skipping read", level='verbose')
                return
            
            self._last_mtime = current_mtime
            port = self._read_port_file()
            
            if port is None:
                self._log("Could not read valid port from file", level='normal')
                return
            
            self._log(f"Read port: {port}, Last port: {self._last_port}", level='verbose')
            
            if port == self._last_port:
                self._log("Port unchanged", level='verbose')
                return
            
            # Check if Nicotine+ already has this port configured
            try:
                current_port_range = self.config.sections["server"]["portrange"]
                
                if current_port_range == (port, port):
                    self._log(f"Port {port} already configured in Nicotine+", level='normal')
                    self._last_port = port
                else:
                    self._log(f"New port detected: {port} (was: {self._last_port})", level='normal')
                    self.update_port(port)
                    self._last_port = port
            except (KeyError, AttributeError) as e:
                self._log(f"Error accessing Nicotine+ config: {e}", level='minimal')
                
        except Exception as e:
            self._log(f"Error checking port: {e}", level='minimal')
        finally:
            # Schedule the next check
            self._log("Check complete, scheduling next check", level='verbose')
            self.schedule_check()
    
    def _read_port_file(self):
        """Read and validate port from file"""
        port_file = self.settings['port_file']
        
        try:
            with open(port_file, 'r') as f:
                line = f.read().strip()
                
                if not line:
                    self._log("Port file is empty", level='verbose')
                    return None
                
                # File format is: "PORT EXPIRY_TIMESTAMP"
                # We only need the first value (the port)
                parts = line.split()
                if not parts:
                    self._log("Port file has no data", level='verbose')
                    return None
                
                port = int(parts[0])
                
                # Validate port range
                if not (1024 <= port <= 65535):
                    self._log(f"Port {port} out of valid range (1024-65535)", level='minimal')
                    return None
                
                # Check expiry timestamp if it exists
                if len(parts) > 1:
                    try:
                        expiry = int(parts[1])
                        if expiry < time.time():
                            self._log(f"Port {port} has expired at {time.ctime(expiry)}", level='normal')
                            return None
                        else:
                            time_remaining = expiry - time.time()
                            self._log(f"Port {port} expires in {int(time_remaining/60)} minutes", level='verbose')
                    except ValueError:
                        self._log("Could not parse expiry timestamp", level='verbose')
                
                return port
                    
        except ValueError as e:
            self._log(f"Cannot parse port number: {e}", level='minimal')
            return None
        except IOError as e:
            self._log(f"Cannot read port file: {e}", level='minimal')
            return None
        except Exception as e:
            self._log(f"Unexpected error reading port file: {e}", level='minimal')
            return None
    
    def update_port(self, port):
        """Update Nicotine+ port configuration"""
        try:
            # Update port range in config
            self.config.sections["server"]["portrange"] = (port, port)
            
            # Reconnect to apply the new port if auto_reconnect is enabled
            if self.settings.get('auto_reconnect', True):
                self._log(f"Reconnecting with new port {port}", level='normal')
                self.core.reconnect()
            else:
                self._log(f"Port set to {port} (auto-reconnect disabled)", level='normal')
            
            new_port_range = self.config.sections["server"]["portrange"]
            self._log(f"Port configuration updated to {new_port_range}", level='normal')
            
        except AttributeError as e:
            self._log(f"Error: reconnect() method not available. Required Nicotine+ version is 3.3.7+", level='minimal')
        except Exception as e:
            self._log(f"Error updating port: {e}", level='minimal')
    
    def disable(self):
        """Stop the timer when plugin is disabled"""
        self._log("Disabling PIA Port Updater", level='normal')
        self._running = False
        
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None
    
    def settings_changed(self):
        """Called when plugin settings are changed"""
        self._log("Settings changed, rescheduling checks", level='verbose')
        # Reschedule with new interval
        self.schedule_check()
    
    def __del__(self):
        """Clean up when plugin is destroyed"""
        self._running = False
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
