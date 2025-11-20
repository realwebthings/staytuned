#!/usr/bin/env python3
"""
AI-based Audio Source Separation using Demucs
True extraction, not modification
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Optional, List, Dict
import logging

import librosa
import numpy as np
import yt_dlp
import click
from tqdm import tqdm
import soundfile as sf
import torch
import torchaudio
from demucs.pretrained import get_model
from demucs.apply import apply_model

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AIAudioExtractor:
    """AI-based source separation using Demucs"""
    
    def __init__(self, model_name: str = "htdemucs", temp_dir: Optional[str] = None):
        # Use provided temp_dir or create one in current directory
        if temp_dir:
            self.temp_dir = temp_dir
            os.makedirs(self.temp_dir, exist_ok=True)
        else:
            self.temp_dir = "./temp_audio"
            os.makedirs(self.temp_dir, exist_ok=True)
        
        self.device = self._get_optimal_device()
        self._optimize_pytorch()
        
        # Load Demucs model
        logger.info(f"Loading {model_name} model...")
        self.model = get_model(model_name)
        self.model.to(self.device)
    
    def _get_optimal_device(self):
        """Auto-detect best available device across all platforms"""
        if torch.backends.mps.is_available():
            logger.info("🚀 Using Apple Silicon GPU (MPS)")
            return torch.device("mps")
        elif torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            logger.info(f"🚀 Using NVIDIA GPU: {gpu_name}")
            return torch.device("cuda")
        else:
            cpu_threads = torch.get_num_threads()
            logger.info(f"💻 Using CPU with {cpu_threads} threads")
            return torch.device("cpu")
    
    def _optimize_pytorch(self):
        """Apply platform-specific optimizations"""
        # CPU optimizations
        if self.device.type == "cpu":
            torch.set_num_threads(torch.get_num_threads())
        
        # CUDA optimizations
        elif self.device.type == "cuda":
            torch.backends.cudnn.benchmark = True
            torch.backends.cudnn.deterministic = False
        
        # MPS optimizations (Apple Silicon)
        elif self.device.type == "mps":
            # MPS-specific optimizations can be added here
            pass
        
    def __del__(self):
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def download_audio(self, url: str, output_path: str) -> str:
        """Download audio from YouTube/streaming platforms"""
        # Create consistent download directory
        download_dir = os.path.join(output_path, "downloads")
        os.makedirs(download_dir, exist_ok=True)
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(download_dir, 'downloaded_audio.%(ext)s'),
            'noplaylist': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore
                info = ydl.extract_info(url, download=True)
                downloaded_file = os.path.join(download_dir, 'downloaded_audio.wav')
                return downloaded_file
        except Exception as e:
            logger.error(f"Download failed: {e}")
            raise
    
    def separate_sources(self, audio_path: str, output_dir: str, start_time: float = None, duration: float = None) -> Dict[str, str]:
        """Separate audio sources using AI"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            # Load audio using librosa (more compatible)
            logger.info("Loading audio...")
            y, sample_rate = librosa.load(audio_path, sr=44100, mono=False)
            
            # Ensure stereo and convert to torch tensor
            if y.ndim == 1:
                y = np.stack([y, y])
            
            # Apply time limits if specified
            if start_time or duration:
                start_frame = int(start_time * sample_rate) if start_time else 0
                end_frame = start_frame + int(duration * sample_rate) if duration else y.shape[1]
                y = y[:, start_frame:end_frame]
            
            waveform = torch.from_numpy(y).float()
            
            # Ensure stereo
            if waveform.shape[0] == 1:
                waveform = waveform.repeat(2, 1)
            
            # Move to device
            waveform = waveform.to(self.device)
            
            # Apply Demucs model
            logger.info("Separating sources with AI...")
            with torch.no_grad():
                sources = apply_model(self.model, waveform.unsqueeze(0), device=self.device)[0]
            
            # Move back to CPU
            sources = sources.cpu()
            
            # Save separated sources
            results = {}
            base_name = Path(audio_path).stem
            source_names = ['drums', 'bass', 'other', 'vocals']
            
            for i, source_name in enumerate(source_names):
                if i < sources.shape[0]:
                    output_path = os.path.join(output_dir, f"{base_name}_{source_name}.wav")
                    # Convert to numpy and save with soundfile
                    audio_data = sources[i].numpy()
                    sf.write(output_path, audio_data.T, sample_rate)
                    results[source_name] = output_path
            
            # Create pure instrumental (everything except vocals)
            if len(source_names) >= 4:
                instrumental = sources[0] + sources[1] + sources[2]  # drums + bass + other
                instrumental_path = os.path.join(output_dir, f"{base_name}_pure_instrumental.wav")
                # Convert to numpy and save with soundfile
                instrumental_data = instrumental.numpy()
                sf.write(instrumental_path, instrumental_data.T, sample_rate)
                results["pure_instrumental"] = instrumental_path
            
            logger.info("AI separation completed!")
            return results
            
        except Exception as e:
            logger.error(f"AI separation failed: {e}")
            raise
    
    def process_batch(self, input_paths: List[str], output_dir: str) -> Dict[str, Dict[str, str]]:
        """Process multiple audio files"""
        results = {}
        
        for audio_path in tqdm(input_paths, desc="Processing files"):
            try:
                file_name = Path(audio_path).stem
                file_output_dir = os.path.join(output_dir, file_name)
                
                file_results = self.separate_sources(audio_path, file_output_dir)
                results[audio_path] = file_results
                
            except Exception as e:
                logger.error(f"Failed to process {audio_path}: {e}")
                results[audio_path] = {"error": str(e)}
        
        return results

@click.command()
@click.option('--input', '-i', help='Input audio file')
@click.option('--output', '-o', default='./output', help='Output directory')
@click.option('--batch', '-b', help='Process multiple files from directory')
@click.option('--url', '-u', help='Download and process from URL')
@click.option('--start-time', '-s', type=float, help='Start time in seconds')
@click.option('--duration', '-d', type=float, help='Duration in seconds')
@click.option('--model', '-m', default='htdemucs', 
              type=click.Choice(['htdemucs', 'htdemucs_ft', 'mdx_extra']),
              help='AI model to use')
def main(input, output, batch, url, start_time, duration, model):
    """AI-powered Audio Source Separation"""
    
    extractor = AIAudioExtractor(model)
    
    try:
        if url:
            logger.info(f"Downloading from URL: {url}")
            temp_audio = extractor.download_audio(url, extractor.temp_dir)
            input = temp_audio
        
        if batch:
            audio_files = []
            for ext in ['*.wav', '*.mp3', '*.flac', '*.m4a']:
                audio_files.extend(Path(batch).glob(ext))
            
            if not audio_files:
                logger.error(f"No audio files found in {batch}")
                return
            
            results = extractor.process_batch([str(f) for f in audio_files], output)
            logger.info(f"Processed {len(results)} files")
            
        elif input:
            if not os.path.exists(input):
                logger.error(f"Input file not found: {input}")
                return
            
            results = extractor.separate_sources(input, output, start_time, duration)
            logger.info("AI separation completed!")
            
            for source, path in results.items():
                logger.info(f"{source}: {path}")
        
        else:
            logger.error("Please provide input file, batch directory, or URL")
            
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()