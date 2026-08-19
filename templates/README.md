# Card Templates

This directory contains starting points for new card applications.

## `custom_card.py`

[custom_card.py](custom_card.py) is an executable minimal card. Copy it into your own project, rename the class, and add widgets to `content_layout`.

It uses `run_card()` so the close button and Ctrl+C terminate the application cleanly.

## `custom_card.json`

[custom_card.json](custom_card.json) is the companion window-configuration template. Copy it to:

```text
~/config/pyqt6-cards/<your-script-name>.json
```

For example, `my_card.py` reads `~/config/pyqt6-cards/my_card.json`. The JSON file can set `width`, `height`, and `position`; see the root [README](../README.md) for the full format.