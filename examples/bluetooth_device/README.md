# Bluetooth Device Dashboard Example

This Linux-only example demonstrates a stateful card that integrates an external command-line service. It monitors one Bluetooth device through BlueZ `bluetoothctl` and presents live state plus connect/disconnect controls. It is not part of the cross-platform `card_widget` package.

## Files

- [joycon_card.py](joycon_card.py): executable entry point configured for a Joy-Con
- [device_card.py](device_card.py): `BluetoothDeviceCard`, the PyQt6 dashboard UI
- [monitor.py](monitor.py): long-lived `bluetoothctl` process and daemon reader thread

## Requirements

```bash
sudo apt install bluez python3-pyqt6 libxcb-cursor0
```

Set `JOYCON_MAC` in [joycon_card.py](joycon_card.py) to the target device address, then run:

```bash
./examples/bluetooth_device/joycon_card.py
```

The device must be awake and able to accept a connection. This example does not bypass device-side power-saving behavior.

## Lifecycle

`BluetoothMonitor` starts one interactive `bluetoothctl` process and reads its stdout from a daemon thread. It emits a Qt signal only when the device state changes. Closing the card stops the resynchronization timer, sends `quit` to `bluetoothctl`, and joins the reader thread.