"""Read temperatures from an MCC E-TC thermocouple device.

The wrapper keeps the dashboard usable when the MCC library or hardware is
unavailable by falling back to simulated channel values.
"""

import time

try:
    from mcculw.enums import TempScale
except Exception:
    class TempScale:
        """Fallback temperature scale constants when MCC UL is missing."""

        CELSIUS = "CELSIUS"


class MCCThermocouple:
    """Interface to an MCC E-TC Ethernet thermocouple device.

    Attributes:
        connected (bool): Whether the device is currently usable.
        simulation_mode (bool): Whether reads are simulated.
        last_error (str | None): Last connection or read error.
    """

    def __init__(self, device_ip=None, device_id=None, board_num=0):
        """Initialize connection metadata and load the MCC library.

        Args:
            device_ip (str, optional): Device IP address for display.
            device_id (str, optional): Optional external device id.
            board_num (int, optional): InstaCal board number to read.
        """

        self.device_ip = device_ip
        self.device_id = device_id
        self.board_num = board_num
        self.connected = False
        self.ul = None
        self.last_error = None
        self.simulation_mode = False
        self._last_logged_error = None

        try:
            from mcculw import ul
            self.ul = ul
        except Exception as e:
            self.last_error = f"mcculw library unavailable: {e}"
            self._log_once(self.last_error)
            self.ul = None

    def _log_once(self, message):
        """Print a repeated hardware error only when it changes."""

        if message != self._last_logged_error:
            print(message)
            self._last_logged_error = message

    def connect(self):
        """Mark the configured MCC board as available.

        Returns:
            bool: ``True`` when the MCC library is available.
        """

        if not self.ul:
            self.connected = False
            self.simulation_mode = True
            self.last_error = "mcculw library not available. Using simulation mode."
            self._log_once(self.last_error)
            return False

        try:
            if self.device_ip:
                print(f"Device IP: {self.device_ip}")
            print(f"Board Number: {self.board_num}")
            print("mcculw import available")
            print("Assuming device configured in InstaCal / MCC software")
            self.connected = True
            self.simulation_mode = False
            self.last_error = None
            self._last_logged_error = None
            return True
        except Exception as e:
            self.last_error = f"Could not connect to MCC device: {e}"
            self._log_once(self.last_error)
            self.connected = False
            self.simulation_mode = True
            return False

    def _simulate(self, count):
        """Create deterministic-looking fallback channel readings."""

        try:
            import numpy as np
            noise = np.random.normal(0, 0.5, count)
        except Exception:
            import random
            noise = [random.gauss(0, 0.5) for _ in range(count)]

        base_temps = [72.5 + (2.0 * index) for index in range(count)]
        return [temp + n for temp, n in zip(base_temps, noise)]

    def read_channels(self, channels=None):
        """Read one or more thermocouple channels.

        Args:
            channels (list[int], optional): MCC channel numbers to read.

        Returns:
            list[float | None]: Temperatures for requested channels.
        """

        if channels is None:
            channels = [0, 1, 2]

        if not self.connected or not self.ul or self.simulation_mode:
            return self._simulate(len(channels))

        try:
            readings = []
            failures = 0
            failure_messages = []

            for ch in channels:
                try:
                    temp = self.ul.t_in(self.board_num, ch, TempScale.CELSIUS)
                    readings.append(float(temp))
                except Exception as ch_error:
                    readings.append(None)
                    failures += 1
                    failure_messages.append(f"ch{ch}: {ch_error}")

            if failures == len(channels):
                self.simulation_mode = True
                self.last_error = "All hardware channel reads failed; using simulated data."
                details = " | ".join(failure_messages)
                self._log_once(f"{self.last_error} Details: {details}")
                return self._simulate(len(channels))

            if failures > 0:
                self.last_error = f"Partial read failure on {failures} channel(s)."
                self._log_once(self.last_error)

            return readings

        except Exception as e:
            self.simulation_mode = True
            self.last_error = f"Error reading channels: {e}"
            self._log_once(self.last_error)
            return self._simulate(len(channels))

    def read_single_channel(self, channel=0):
        """Read a single thermocouple channel."""

        values = self.read_channels([channel])
        return values[0] if values else None

    def read_all_channels(self):
        """Read all eight MCC E-TC channels."""

        return self.read_channels(channels=[0, 1, 2, 3, 4, 5, 6, 7])

    def disconnect(self):
        """Close the logical hardware connection.

        Returns:
            bool: Always ``True`` after the connection state is cleared.
        """

        if not self.connected:
            return True
        self.connected = False
        self.simulation_mode = True
        self._log_once("Disconnected from MCC E-TC device")
        return True

    def get_device_info(self):
        """Return device metadata for status displays."""

        return {
            "device_id": self.device_id,
            "device_ip": self.device_ip,
            "board_num": self.board_num,
            "connected": self.connected,
            "simulation_mode": self.simulation_mode,
            "channels": 8,
            "sampling_rate_max": 1000,
            "last_error": self.last_error,
        }

    def test_read(self):
        """Run a console smoke test for channels 0 through 2."""

        print("\n=== MCC E-TC Hardware Test ===")
        print(f"Device IP: {self.device_ip}")
        print(f"Board Number: {self.board_num}")

        if not self.connect():
            print("Failed to connect to device")
            return False

        print("\nReading channels 0, 1, 2...")
        temps = self.read_channels([0, 1, 2])

        if temps:
            print(f"Channel 0: {temps[0] if temps[0] is not None else 'N/A'}")
            print(f"Channel 1: {temps[1] if temps[1] is not None else 'N/A'}")
            print(f"Channel 2: {temps[2] if temps[2] is not None else 'N/A'}")
            if self.simulation_mode:
                print("Hardware unavailable; currently using simulated data")
            else:
                print("Hardware test complete")
            self.disconnect()
            return True

        print("Failed to read channels")
        return False


if __name__ == "__main__":
    device = MCCThermocouple(device_ip="192.168.10.101", board_num=0)
    device.test_read()
