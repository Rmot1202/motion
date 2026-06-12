import time

try:
    import uldaq as ul
except Exception:
    ul = None


class MCCThermocouple:
    def __init__(self, device_ip=None, device_id=None, board_num=0):
        self.device_ip = device_ip
        self.device_id = device_id
        self.board_num = board_num
        self.connected = False
        self.device = None
        self.ai_device = None
        self.last_error = None
        self.simulation_mode = False
        self._last_logged_error = None
        self.ever_had_real_data = False
        self.last_real_data_ts = None

        if ul is None:
            self.last_error = "uldaq library unavailable"
            self._log_once(self.last_error)

    def _log_once(self, message):
        if message != self._last_logged_error:
            print(message)
            self._last_logged_error = message

    def _simulate(self, count):
        try:
            import numpy as np
            noise = np.random.normal(0, 0.5, count)
            return [72.5 + (2.0 * idx) + noise[idx] for idx in range(count)]
        except Exception:
            import random
            return [72.5 + (2.0 * idx) + random.gauss(0, 0.5) for idx in range(count)]

    def _mark_real_data(self):
        self.ever_had_real_data = True
        self.last_real_data_ts = time.time()
        self.simulation_mode = False

    def _real_data_recent(self, timeout_s=30):
        if self.last_real_data_ts is None:
            return False
        return (time.time() - self.last_real_data_ts) <= timeout_s

    def connect(self):
        if ul is None:
            self.connected = False
            self.simulation_mode = True
            self.last_error = "uldaq library not available. Using simulation mode."
            self._log_once(self.last_error)
            return False

        try:
            devices = ul.get_daq_device_inventory(ul.InterfaceType.ETHERNET)
            if not devices:
                devices = ul.get_daq_device_inventory(ul.InterfaceType.ANY)

            if not devices:
                self.connected = False
                self.simulation_mode = True
                self.last_error = "No MCC device found."
                self._log_once(self.last_error)
                return False

            chosen = None
            if self.device_ip:
                for d in devices:
                    d_text = str(d)
                    if self.device_ip in d_text:
                        chosen = d
                        break

            if chosen is None:
                chosen = devices[0]

            self.device = ul.DaqDevice(chosen)
            self.device.connect()
            self.ai_device = self.device.get_ai_device()

            self.connected = True
            self.simulation_mode = False
            self.last_error = None
            self._last_logged_error = None
            print(f"Connected to device: {chosen}")
            return True

        except Exception as e:
            self.last_error = f"Could not connect to MCC device: {e}"
            self._log_once(self.last_error)
            self.connected = False
            self.simulation_mode = True
            return False

    def disconnect(self):
        try:
            if self.device is not None:
                self.device.disconnect()
                self.device.release()
        except Exception:
            pass

        self.device = None
        self.ai_device = None
        self.connected = False
        self.simulation_mode = True
        self._log_once("Disconnected from MCC device")
        return True

    def _read_hardware_channel(self, ch):
        if self.ai_device is None:
            raise RuntimeError("AI device not available")

        return float(
            self.ai_device.a_in(
                ch,
                ul.AiInputMode.SINGLE_ENDED,
                ul.Range.BIP10VOLTS
            )
        )

    def read_channels(self, channels=None):
        if channels is None:
            channels = [0, 1, 2, 3, 4, 5, 6, 7]

        if not self.connected or not self.device:
            self.simulation_mode = True
            self.last_error = "Hardware/library unavailable; using simulated data."
            self._log_once(self.last_error)
            return self._simulate(len(channels))

        try:
            readings = []
            failures = 0
            failure_messages = []

            for ch in channels:
                try:
                    value = self._read_hardware_channel(ch)
                    readings.append(float(value))
                except Exception as ch_error:
                    readings.append(None)
                    failures += 1
                    failure_messages.append(f"ch{ch}: {ch_error}")

            any_real = any(v is not None for v in readings)

            if any_real:
                self._mark_real_data()
                if failures > 0:
                    self.last_error = f"Partial read failure on {failures} channel(s)."
                    self._log_once(self.last_error)
                return readings

            if self._real_data_recent(timeout_s=30):
                self.simulation_mode = False
                self.last_error = "No current real data, but real data was seen within 30 seconds."
                details = " | ".join(failure_messages)
                self._log_once(self.last_error + f" Details: {details}")
                return readings

            if not self.ever_had_real_data:
                self.simulation_mode = True
                self.last_error = "No hardware data yet; using simulated data."
                details = " | ".join(failure_messages)
                self._log_once(f"{self.last_error} Details: {details}")
                return self._simulate(len(channels))

            self.simulation_mode = False
            self.last_error = "All channels returned None; returning None values."
            details = " | ".join(failure_messages)
            self._log_once(self.last_error + f" Details: {details}")
            return readings

        except Exception as e:
            self.last_error = f"Error reading channels: {e}"
            self._log_once(self.last_error)

            if not self.ever_had_real_data:
                self.simulation_mode = True
                return self._simulate(len(channels))

            self.simulation_mode = False
            return [None] * len(channels)

    def read_single_channel(self, channel=0):
        values = self.read_channels([channel])
        return values[0] if values else None

    def read_all_channels(self):
        return self.read_channels(channels=[0, 1, 2, 3, 4, 5, 6, 7])

    def get_device_info(self):
        return {
            "device_id": self.device_id,
            "device_ip": self.device_ip,
            "board_num": self.board_num,
            "connected": self.connected,
            "simulation_mode": self.simulation_mode,
            "channels": 8,
            "sampling_rate_max": 1000,
            "last_error": self.last_error,
            "ever_had_real_data": self.ever_had_real_data,
            "last_real_data_ts": self.last_real_data_ts,
            "backend": "uldaq",
        }

    def test_read(self):
        print("\n=== MCC E-TC Hardware Test ===")
        print(f"Device IP: {self.device_ip}")
        print(f"Board Number: {self.board_num}")

        if not self.connect():
            print("Failed to connect to device")
            return False

        print("\nReading all 8 channels...")
        temps = self.read_all_channels()

        for i, value in enumerate(temps):
            print(f"Channel {i}: {value if value is not None else 'N/A'}")

        if self.simulation_mode:
            print("Currently using simulated data")
        else:
            print("Hardware test complete")

        self.disconnect()
        return True


if __name__ == "__main__":
    device = MCCThermocouple(device_ip="192.168.10.101", board_num=0)
    device.test_read()