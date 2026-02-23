# Installation Instructions

## Quick Install (Recommended)

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install all dependencies
pip install -r requirements.txt

# Install demucs without lameenc dependency
pip install demucs --no-deps
```

## Note
Demucs must be installed separately with `--no-deps` because the `lameenc` package is not available for all platforms. All required demucs dependencies are already in requirements.txt.

## Verify Installation
```bash
python3 simple_web_app.py
```

Open http://localhost:8000 in your browser.
