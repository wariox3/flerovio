# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project purpose

Flerovio is a desktop application intended as a replacement for "cromo escritorio" and built as an extension for the **Semántica ERP — Transporte** product. The project description and language are in Spanish — mirror that in code comments, commit messages, and UI strings unless told otherwise.

## Stack

- **Language:** Python ≥3.11 (pure Python desktop app, no web wrapper).
- **UI:** **PySide6** (official Qt for Python binding). Chosen for native UI on Linux/Windows, mature widgets, Qt Designer support, and LGPL.
- **Targets:** Linux and Windows — avoid platform-specific shortcuts.
- **Build backend:** `hatchling` via `pyproject.toml`, `src/` layout.
- **Packaging:** PyInstaller (expect ~40 MB binaries; mind binary-size impact when adding deps).

## Layout

```
src/flerovio/
  __init__.py     # version
  __main__.py     # entry point — exposed as the `flerovio` console script
  app.py          # MainWindow and other UI classes
tests/            # pytest + pytest-qt
pyproject.toml    # deps, dev extras, ruff and pytest config
```

The package is imported as `flerovio` and runnable as `python -m flerovio` or via the installed `flerovio` script.

## Commands

Setup (one-time):

```bash
python3 -m venv ~/.venvs/flerovio
source ~/.venvs/flerovio/bin/activate
pip install -e ".[dev]"
```

The venv lives outside the repo at `~/.venvs/flerovio/` — activate it before running any of the day-to-day commands below.

Day to day:

```bash
python -m flerovio            # run the app
pytest                        # run tests
pytest tests/test_app.py::test_main_window_title   # run a single test
ruff check .                  # lint
ruff format .                 # format
```

Packaging:

```bash
pyinstaller --name flerovio --windowed -m flerovio
```

## Conventions

- Use PySide6 patterns: signals/slots, `QWidget` hierarchy, and `.ui` files designed in Qt Designer loaded via `QUiLoader` when UI grows beyond hand-written widgets.
- Prefer libraries that cooperate with Qt's event loop (e.g., `qasync` if async is needed).
- Link PySide6 dynamically (the default) to stay LGPL-compliant; do not bundle modified Qt.
- Widget tests use `pytest-qt`'s `qtbot` fixture and must call `qtbot.addWidget(w)` so widgets get cleaned up between tests.
