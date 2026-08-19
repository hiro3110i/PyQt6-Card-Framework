# Tests

This directory contains automated checks for framework behavior that does not require a visible desktop session.

## Running Tests

Run the tests from the repository root:

```bash
QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s tests -v
```

## Coverage

[test_settings.py](test_settings.py) verifies per-script JSON configuration:

- the settings filename is derived from the script name without `.py`
- width, height, and coordinate position are applied to a card
- malformed JSON falls back to the code-defined defaults
