# Ollama GUI

A clean, modern desktop GUI for managing local Ollama models — no terminal required.

## Features

- **Dashboard** — Server status, model count, disk usage at a glance
- **Model Management** — List, pull, delete, inspect, and copy models
- **Running Models Monitor** — See what's loaded in memory with VRAM usage
- **Chat / Test Panel** — Quickly test a model's coding ability before using it in VSCode
- **Dark Theme** — Modern dark UI by default

## Requirements

- Python 3.10+
- [Ollama](https://ollama.com/) installed and running

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd ollama_gui

# Create a virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
python -m ollama_gui.app
```

Make sure Ollama is running (`ollama serve`) before launching the GUI.

## Development

```bash
pip install -e ".[dev]"
python -m pytest tests/ -v
```
