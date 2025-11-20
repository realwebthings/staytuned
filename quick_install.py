#!/usr/bin/env python3
"""
Quick installer for StayTuned Audio Extractor
"""

import subprocess
import sys
import platform

def install_package(package):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    print("🎵 Quick Install - StayTuned Audio Extractor")
    
    # Check platform
    if platform.machine() == 'arm64':
        print("✅ Detected Apple Silicon - optimizing installation")
    
    # Essential packages
    packages = [
        "librosa>=0.10.0",
        "yt-dlp>=2023.7.6",
        "numpy>=1.24.0",
        "scipy>=1.11.0",
        "click>=8.1.0",
        "tqdm>=4.65.0",
        "soundfile>=0.12.0",
        "fastapi>=0.104.0",
        "uvicorn>=0.24.0",
        "python-multipart>=0.0.6",
        "jinja2>=3.1.0",
        "torch>=2.1.0",
        "torchaudio>=2.1.0",
        "demucs>=4.0.0"
    ]
    
    print("📦 Installing packages...")
    
    failed_packages = []
    for package in packages:
        print(f"Installing {package}...")
        if not install_package(package):
            failed_packages.append(package)
    
    if failed_packages:
        print(f"❌ Failed to install: {', '.join(failed_packages)}")
        print("Try installing manually")
    else:
        print("✅ All packages installed successfully!")
        
        # Test imports
        print("🧪 Testing imports...")
        try:
            import librosa
            import yt_dlp
            import soundfile as sf
            import torch
            
            # Check GPU support
            if torch.backends.mps.is_available():
                print("🚀 Apple Silicon GPU (MPS) ready!")
            elif torch.cuda.is_available():
                print("🚀 NVIDIA GPU ready!")
            else:
                print("💻 Using CPU")
            
            print("\n🚀 Installation complete!")
            print("Usage:")
            print("  python3 simple_web_app.py  # Simple web interface")
            print("  python3 ai_extractor.py -i song.mp3 -o ./output  # AI separation")
            
        except ImportError as e:
            print(f"❌ Import failed: {e}")

if __name__ == "__main__":
    main()