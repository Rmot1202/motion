"""Shared pytest fixtures for thermocouple hardware tests."""

import pytest
from appilcation.hardware import MCCThermocouple

@pytest.fixture
def device():
    """Yield a connected MCC device or skip when unavailable."""

    dev = MCCThermocouple()
    if not dev.connect():
        pytest.skip("Thermocouple device not connected")
    yield dev
    dev.disconnect()
