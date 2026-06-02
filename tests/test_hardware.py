#!/usr/bin/env python3
"""
MCC E-TC Hardware Test Script

This script tests communication with the MCC E-TC thermocouple device.
Run this before starting the main dashboard to verify hardware connection.

Usage:
    python test_hardware.py              # Test with defaults (board 0)
    python test_hardware.py 192.168.1.100  # Test specific IP
    python test_hardware.py 192.168.1.100 1  # Test specific IP and board
"""

import sys
import time
from appilcation.hardware import MCCThermocouple


def print_header(text):
    """Print formatted header."""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)


def print_status(icon, message):
    """Print status message with icon."""
    print(f"{icon} {message}")


def test_basic_connection(device):
    """Test basic device connection."""
    print_header("STEP 1: Device Connection Test")
    
    device_info = device.get_device_info()
    print_status("ℹ", f"Device IP: {device_info['device_ip']}")
    print_status("ℹ", f"Board Number: {device_info['board_num']}")
    
    print("\nAttempting connection...")
    assert device.connect()
    print_status("✓", "Device connected successfully!")


def test_single_read(device):
    """Test single channel reading."""
    print_header("STEP 2: Single Channel Read Test")
    
    print("Reading channel 0...")
    temp = device.read_single_channel(channel=0)
    assert temp is not None
    print_status("✓", f"Channel 0: {temp:.2f}°C")


def test_multi_read(device):
    """Test reading multiple channels."""
    print_header("STEP 3: Multi-Channel Read Test")
    
    channels = [0, 1, 2]
    print(f"Reading channels {channels}...")
    
    temps = device.read_channels(channels)
    assert temps and all(t is not None for t in temps)
    for i, temp in enumerate(temps):
        print_status("✓", f"Channel {i}: {temp:.2f}°C")


def test_continuous_read(device, duration=10, interval=1):
    """Test continuous reading."""
    print_header(f"STEP 4: Continuous Read Test ({duration}s)")
    
    print(f"Reading every {interval}s for {duration}s...\n")
    print("Time(s) | Ch0(°C)   | Ch1(°C)   | Ch2(°C)   | Status")
    print("-" * 60)
    
    start_time = time.time()
    read_count = 0
    success_count = 0
    
    try:
        while time.time() - start_time < duration:
            elapsed = time.time() - start_time
            temps = device.read_channels([0, 1, 2])
            read_count += 1
            
            assert temps and all(t is not None for t in temps)
            success_count += 1
            status = "✓ OK"
            print(f"{elapsed:6.1f}  | {temps[0]:9.2f} | {temps[1]:9.2f} | {temps[2]:9.2f} | {status}")
            
            time.sleep(interval)
    
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    
    print("-" * 60)
    print(f"\nResults: {success_count}/{read_count} reads successful ({100*success_count/read_count:.1f}%)")
    assert success_count == read_count


def test_all_channels(device):
    """Test all 8 available channels."""
    print_header("STEP 5: All Channels Test (Optional)")
    
    print("Reading all 8 channels...")
    temps = device.read_all_channels()
    assert temps
    for i, temp in enumerate(temps):
        if temp is not None:
            print_status("✓", f"Channel {i}: {temp:.2f}°C")
        else:
            print_status("⚠", f"Channel {i}: Not connected or error")


def run_full_test(device_ip=None, board_num=0):
    """Run complete hardware test suite."""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*15 + "MCC E-TC HARDWARE TEST SUITE" + " "*14 + "║")
    print("╚" + "="*58 + "╝")
    
    # Create device instance
    device = MCCThermocouple(device_ip=device_ip, board_num=board_num)
    
    # Run tests
    tests = [
        ("Connection", test_basic_connection),
        ("Single Channel Read", test_single_read),
        ("Multi-Channel Read", test_multi_read),
        ("Continuous Read (10s)", test_continuous_read),
        ("All Channels", test_all_channels),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            if test_name == "Continuous Read (10s)":
                test_func(device, duration=10, interval=1)
            else:
                test_func(device)
            results.append((test_name, True))
        except Exception as e:
            print_status("✗", f"Test error: {e}")
            results.append((test_name, False))
    
    # Summary
    print_header("TEST SUMMARY")
    
    total_tests = len(results)
    passed_tests = sum(1 for _, result in results if result)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print_status("", f"{test_name:30} {status}")
    
    print("\n" + "-"*60)
    print(f"Total: {passed_tests}/{total_tests} tests passed\n")
    
    # Recommendations
    if passed_tests == total_tests:
        print_status("✓", "All tests passed! Hardware is ready.")
        print("\nNext step: Run the dashboard")
        print("  python app.py")
    else:
        print_status("⚠", "Some tests failed. Check hardware connection.")
        print("\nTroubleshooting:")
        print("  1. Verify device is connected via Ethernet")
        print("  2. Check IP address in config.py")
        print("  3. Ensure MCC device manager shows device as connected")
        print("  4. Verify mcculw library is installed: pip install mcculw")
    
    # Cleanup
    device.disconnect()
    
    return passed_tests == total_tests


if __name__ == "__main__":
    device_ip = None
    board_num = 0
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        device_ip = sys.argv[1]
        print(f"Using device IP: {device_ip}")
    
    if len(sys.argv) > 2:
        board_num = int(sys.argv[2])
        print(f"Using board number: {board_num}")
    
    # Run tests
    success = run_full_test(device_ip=device_ip, board_num=board_num)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
