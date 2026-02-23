# StayTuned - Audio Instrumental Extractor

Extract instrumental tracks from songs, videos, and audio files from local sources, YouTube, or streaming platforms.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Web Interface (Recommended)
python3 simple_web_app.py
# Then open http://localhost:8000

# Command Line
python3 ai_extractor.py -i song.mp3 -o ./output
python3 ai_extractor.py -u "https://youtube.com/watch?v=..." -o ./output
```

## Features

- **Web Interface**: Easy-to-use browser interface with drag & drop
- **Multi-source Support**: Local files, YouTube, streaming URLs
- **Video Download**: Optional video download from YouTube and other platforms
- **Advanced Controls**: Vocal reduction strength, frequency filtering
- **Multiple Output Formats**: 6 different extraction methods
- **Batch Processing**: Process multiple files simultaneously
- **Python 3.13 Compatible**: Works with latest Python versions

## Installation

```bash
pip install -r requirements.txt

# Install FFmpeg (required for audio processing)
# macOS: brew install ffmpeg
# Ubuntu: sudo apt install ffmpeg
# Windows: Download from https://ffmpeg.org
```

## Usage Examples

```bash
# Basic AI separation
python3 ai_extractor.py -i "song.mp3" -o "./output"

# From YouTube (audio only)
python3 ai_extractor.py -u "https://youtube.com/watch?v=..." -o "./output"

# From YouTube with video download
python3 ai_extractor.py -u "https://youtube.com/watch?v=..." --download-video -o "./output"

# Extract 30 seconds starting from 1 minute
python3 ai_extractor.py -i "song.mp3" -o "./output" -s 60 -d 30

# Batch processing
python3 ai_extractor.py -b "./music_folder" -o "./output"

# Different AI models
python3 ai_extractor.py -i "song.mp3" -o "./output" -m htdemucs_ft
```

## Output Files

For each input, you get 4 clean separated tracks:
- `*_vocals_only.wav` - Isolated vocal track
- `*_pure_instrumental.wav` - Clean instrumental (perfect for background music)
- `*_drums_only.wav` - Drums and percussion only
- `*_harmonic_instruments.wav` - Melody instruments and chords

## Advanced Controls

- `--vocal-reduction` (`-v`): Strength of vocal removal (0.0-1.0, default 0.8)
- `--freq-range` (`-f`): Frequency range to keep (default "80,8000")
- `--start-time` (`-s`): Start time in seconds
- `--duration` (`-d`): Duration in seconds

**Examples:**
- `-v 1.0` = Maximum vocal removal (may affect instruments)
- `-v 0.5` = Gentle vocal reduction (keeps more original sound)
- `-f "100,6000"` = Remove deep bass and very high frequencies
- `-f "200,4000"` = Focus on mid-range instruments only
- `-s 60 -d 30` = Extract 30 seconds starting from 1 minute
- `-s 0 -d 60` = Extract first minute only

## Requirements

- Python 3.8+
- FFmpeg
- 2GB+ RAM recommended

## Supported Formats

- **Input**: WAV, MP3, FLAC, M4A, OGG
- **Output**: WAV (high quality)
- **Sources**: Local files, YouTube, most streaming platforms