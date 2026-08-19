# Examples

This directory contains runnable reference implementations for the framework. They are intended to show the shape of a card application, not to define the framework API.

## Included Examples

- [clock_card.py](clock_card.py): a minimal card with a timer-driven label
- [bluetooth_device/](bluetooth_device): a complete device dashboard with subprocess and reader-thread lifecycle management

Run a script from the repository root or execute it directly:

```bash
./examples/clock_card.py
```

Each runnable script resolves `card_widget` from the current checkout. See the root [README](../README.md) for requirements and per-script window configuration.