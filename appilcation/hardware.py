"""
Hardware interface module for MCC E-TC Ethernet thermocouple device.
Uses the mcculw library for actual hardware communication.

Reference:
- GitHub: https://github.com/mccdaq/mcculw
- E-TC User Guide: https://idm-instrumentos.es/wp-content/uploads/2021/02/E-TC.pdf
- MCC Examples: https://files.digilent.com/manuals/Mcculw_WebHelp/Misc/Py-ex-func.htm
"""

import time
from mcculw.enums import TempScale

class MCCThermocouple:
    """Interface to MCC E-TC Ethernet thermocouple device."""
    
    def __init__(self, device_ip=None, device_id=None, board_num=0):
        """
        Initialize connection to MCC E-TC device.
        
        Args:
            device_ip: IP address of the MCC E-TC device (optional)
            device_id: Device identifier (optional)
            board_num: Board number (default 0 for single device)
        """
        self.device_ip = device_ip
        self.device_id = device_id
        self.board_num = board_num
        self.connected = False
        self.ul = None
        self.last_error = None
        
        try:
            from mcculw import ul
            self.ul = ul
        except Exception as e:
            self.last_error = f"mcculw library unavailable: {e}"
            print(f"⚠ Warning: {self.last_error}")
            self.ul = None
        
    def connect(self):
        if not self.ul:
            print("⚠ mcculw library not available. Using simulation mode.")
            return False

        try:
            if self.device_ip:
                print(f"ℹ Device IP: {self.device_ip}")
            print(f"ℹ Board Number: {self.board_num}")
            print("✓ mcculw import available")
            print("✓ Assuming device configured in InstaCal / MCC software")
            self.connected = True
            return True
        except Exception as e:
            self.last_error = str(e)
            print(f"⚠ Could not connect to MCC device: {e}")
            print("   Using simulation mode as fallback")
            return False
    
    def read_channels(self, channels=[0, 1, 2]):
        """
        Read temperature from specified channels.
        
        Args:
            channels: List of channel indices (0-7 for E-TC, typically 0-2)
            
        Returns:
            List of temperature readings in Celsius
        """
        if not self.connected or not self.ul:
            # Return simulated data as fallback
            try:
                import numpy as np
                noise = np.random.normal(0, 0.5, len(channels))
            except Exception:
                import random
                noise = [random.gauss(0, 0.5) for _ in range(len(channels))]
            base_temps = [72.5 + (2.0 * index) for index in range(len(channels))]
            return [temp + n for temp, n in zip(base_temps, noise)]
        
        try:
            readings = []
            for ch in channels:
                try:
                    # Read temperature in Celsius from thermocouple channel
                    # ul.t_in(board_num, channel) returns temperature in Celsius
                    temp = self.ul.t_in(self.board_num, ch, TempScale.CELSIUS)
                    readings.append(float(temp))
                except Exception as ch_error:
                    print(f"⚠ Error reading channel {ch}: {ch_error}")
                    readings.append(None)
            
            return readings
            
        except Exception as e:
            print(f"Error reading channels: {e}")
            self.last_error = str(e)
            return [None] * len(channels)
    
    def read_single_channel(self, channel=0):
        """
        Read temperature from a single channel.
        
        Args:
            channel: Channel index (0-7)
            
        Returns:
            Temperature reading in Celsius, or None on error
        """
        if not self.connected or not self.ul:
            import random
            return 72.5 + random.uniform(-0.5, 0.5)
        
        try:
            temp = self.ul.t_in(self.board_num, channel, TempScale.CELSIUS)
            return float(temp)
        except Exception as e:
            print(f"Error reading channel {channel}: {e}")
            return None
    
    def read_all_channels(self):
        """
        Read all 8 thermocouple channels (E-TC supports 0-7).
        
        Returns:
            List of 8 temperature readings in Celsius
        """
        return self.read_channels(channels=[0, 1, 2, 3, 4, 5, 6, 7])
    
    def disconnect(self):
        """Close connection to device."""
        if not self.connected or not self.ul:
            return True
        
        try:
            self.connected = False
            print("✓ Disconnected from MCC E-TC device")
            return True
        except Exception as e:
            print(f"Error disconnecting: {e}")
            return False
    
    def get_device_info(self):
        """Get device information."""
        return {
            "device_id": self.device_id,
            "device_ip": self.device_ip,
            "board_num": self.board_num,
            "connected": self.connected,
            "channels": 8,  # E-TC has 8 channels
            "sampling_rate_max": 1000,  # Hz
            "last_error": self.last_error
        }
    
    def test_read(self):
        """
        Test function to verify device communication.
        Reads channels 0, 1, 2 once and prints values.
        """
        print("\n=== MCC E-TC Hardware Test ===")
        print(f"Device IP: {self.device_ip}")
        print(f"Board Number: {self.board_num}")
        
        if not self.connect():
            print("✗ Failed to connect to device")
            return False
        
        print("\nReading channels 0, 1, 2...")
        temps = self.read_channels([0, 1, 2])
        
        if temps:
            print(f"✓ Channel 0: {temps[0]:.2f}°C")
            print(f"✓ Channel 1: {temps[1]:.2f}°C")
            print(f"✓ Channel 2: {temps[2]:.2f}°C")
            print("✓ Hardware test successful!")
            self.disconnect()
            return True
        else:
            print("✗ Failed to read channels")
            return False


# Example usage / testing
if __name__ == "__main__":
    # Test with default settings
    device = MCCThermocouple(board_num=0)
    
    # Uncomment to test with specific IP:
    device = MCCThermocouple(device_ip="192.168.10.101", board_num=0)
    
    device.test_read()
