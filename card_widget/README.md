# `card_widget`

This package contains the reusable framework API. It has no knowledge of any particular card domain or data source, and uses PyQt6's cross-platform APIs for Linux, macOS, and Windows.

## Modules

- [base_card.py](base_card.py): `BaseCardWidget`, card chrome, dragging, and initial placement
- [application.py](application.py): `run_card()` application runner and Ctrl+C handling
- [settings.py](settings.py): per-script JSON configuration lookup and parsing

## Use

Import the public API from the package root:

```python
from card_widget import BaseCardWidget, InitialPosition, run_card
```

Use `closing` to shut down card-specific resources such as timers, subprocesses, or worker threads before the window closes.

See the repository [README](../README.md) for a quick start and configuration format.