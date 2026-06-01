# MCCThermocouple in C

This project provides a small C-style wrapper for reading temperatures from an MCC E-TC Ethernet thermocouple device. It is based on Measurement Computing's Universal Library, which supports C/C++ and related native language interfaces for Windows applications [web:882][web:896].

## Overview

The MCC E-TC is an Ethernet-based, 8-channel thermocouple measurement device designed for temperature acquisition [web:887][web:890]. In C, the same design used in the Python version becomes a struct or object-like wrapper that manages connection state, reads channels, handles errors, and optionally falls back to simulated values during development [web:896][web:897].

## Features

- Connect to an MCC thermocouple device through the Universal Library [web:882][web:889].
- Read one or more channels in Celsius [web:896][web:897].
- Read all available channels.
- Support partial read failures by returning invalid channels as missing values.
- Switch to simulation mode when hardware or library access fails.
- Expose basic device information for diagnostics or dashboards.

## Requirements

- Windows operating system.
- MCC Universal Library installed [web:882][web:889].
- MCC device configured in InstaCal or MCC software [web:895][web:883].
- A C compiler such as Visual Studio or another Windows C/C++ toolchain [web:882][web:896].

## Example API

### Struct

```c
typedef struct {
    const char* device_ip;
    int device_id;
    int board_num;
    int connected;
    int simulation_mode;
    const char* last_error;
} MCCThermocouple;
```

### Core functions

```c
int mcct_connect(MCCThermocouple* dev);
int mcct_read_channels(MCCThermocouple* dev, int* channels, int channel_count, double* values);
double mcct_read_single_channel(MCCThermocouple* dev, int channel);
int mcct_read_all_channels(MCCThermocouple* dev, double* values, int max_channels);
int mcct_disconnect(MCCThermocouple* dev);
void mcct_get_device_info(MCCThermocouple* dev);
```

## Example usage

```c
#include <stdio.h>

int main(void) {
    MCCThermocouple dev;
    dev.device_ip = "192.168.10.101";
    dev.device_id = 0;
    dev.board_num = 0;
    dev.connected = 0;
    dev.simulation_mode = 0;
    dev.last_error = NULL;

    if (mcct_connect(&dev)) {
        double temps;
        int channels = {0, 1, 2};

        if (mcct_read_channels(&dev, channels, 3, temps)) {
            printf("Channel 0: %.3f\n", temps);
            printf("Channel 1: %.3f\n", temps);
            printf("Channel 2: %.3f\n", temps);
        }

        mcct_disconnect(&dev);
    } else {
        printf("Connection failed, using simulation mode.\n");
    }

    return 0;
}
```

## Behavior

### Connection
The `connect` function initializes access to the MCC library and device. If the library is missing or the device cannot be reached, the wrapper can switch into simulation mode.

### Channel reads
The `read_channels` function retrieves thermocouple values in Celsius. The Universal Library documentation shows that thermocouple input functions can also include error handling for open thermocouples and out-of-range values [web:896].

### Simulation mode
If hardware access is unavailable, simulated values can be generated so the application continues to run during development.

## Notes

This C version is conceptually the same as the Python version, just with explicit types and functions instead of Python methods. The Universal Library documentation supports C/C++ use cases, and the MCC E-TC product line is designed for multi-channel thermocouple measurement over Ethernet [web:882][web:896][web:887].