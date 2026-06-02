# tests/conftest.py
import pytest
from appilcation.hardware import MCCThermocouple

@pytest.fixture
def device():
    dev = MCCThermocouple()
    if not dev.connect():
        pytest.skip("Thermocouple device not connected")
    yield dev
    dev.disconnect()