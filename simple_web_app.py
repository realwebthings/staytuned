#!/usr/bin/env python3
"""
Simple Web Interface for StayTuned Audio Extractor
Uses only the working AI extractor without problematic dependencies
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import tempfile
import shutil
from pathlib import Path
import asyncio
import traceback
from ai_extractor import AIAudioExtractor

app = FastAPI(title="StayTuned Audio Extractor")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Create output directory
OUTPUT_DIR = Path("./web_output")
OUTPUT_DIR.mkdir(exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def main(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/extract-file")
async def extract_file(file: UploadFile = File(...)):
    """Extract audio from uploaded file"""
    if not file.filename or not file.filename.lower().endswith(('.mp3', '.wav', '.flac', '.m4a', '.ogg')):
        raise HTTPException(status_code=400, detail="Unsupported file format")
    
    # Save uploaded file
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
        shutil.copyfileobj(file.file, tmp_file)
        temp_path = tmp_file.name
    
    try:
        # Extract audio (run in thread pool)
        def run_extraction():
            extractor = AIAudioExtractor()
            results = extractor.separate_sources(temp_path, str(OUTPUT_DIR))
            return list(results.values())
        
        output_files = await asyncio.to_thread(run_extraction)
        
        # Get just filenames for response
        file_names = [Path(f).name for f in output_files]
        
        return {"status": "success", "files": file_names}
    
    except Exception as e:
        print(f"Extraction error: {e}")
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")
    
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.unlink(temp_path)

@app.post("/extract-url")
async def extract_url(data: dict):
    """Extract audio from YouTube URL with optional video download"""
    url = data.get("url")
    download_video = data.get("download_video", False)
    extract_audio = data.get("extract_audio", True)
    
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    
    # Validate at least one option is selected
    if not extract_audio and not download_video:
        raise HTTPException(status_code=400, detail="At least one option must be selected")
    
    # Prevent concurrent processing of same URL
    import hashlib
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    
    try:
        # Extract audio (run in thread pool)
        def run_extraction():
            # Use controlled temp directory with URL hash
            temp_dir = str(OUTPUT_DIR / "temp" / url_hash)
            extractor = AIAudioExtractor(temp_dir=temp_dir)
            
            response_files = []
            
            # Download audio if requested
            if extract_audio:
                download_results = extractor.download_audio(url, str(OUTPUT_DIR), download_video, download_audio=True)
                temp_audio = download_results['audio']
                
                # Separate audio sources
                results = extractor.separate_sources(temp_audio, str(OUTPUT_DIR))
                
                # Clean up temp audio file
                if os.path.exists(temp_audio):
                    os.unlink(temp_audio)
                
                response_files.extend(list(results.values()))
                
                # Add video file if downloaded
                if download_video and 'video' in download_results:
                    video_file = download_results['video']
                    if os.path.exists(video_file):
                        video_name = f"video_{url_hash}{Path(video_file).suffix}"
                        final_video_path = OUTPUT_DIR / video_name
                        shutil.copy2(video_file, final_video_path)
                        response_files.append(str(final_video_path))
                        os.unlink(video_file)
            
            # Download only video (no audio extraction)
            elif download_video:
                download_results = extractor.download_audio(url, str(OUTPUT_DIR), download_video=True, download_audio=False)
                
                if 'video' in download_results:
                    video_file = download_results['video']
                    if os.path.exists(video_file):
                        video_name = f"video_{url_hash}{Path(video_file).suffix}"
                        final_video_path = OUTPUT_DIR / video_name
                        shutil.copy2(video_file, final_video_path)
                        response_files.append(str(final_video_path))
                        os.unlink(video_file)
            
            return response_files
        
        output_files = await asyncio.to_thread(run_extraction)
        
        # Get just filenames for response
        file_names = [Path(f).name for f in output_files]
        
        return {"status": "success", "files": file_names, "has_video": download_video}
    
    except Exception as e:
        error_msg = f"URL extraction error: {e}"
        print(error_msg)
        print(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/stream/{filename}")
async def stream_file(filename: str):
    """Stream audio/video file for in-browser playback"""
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Determine media type based on file extension
    file_ext = Path(filename).suffix.lower()
    if file_ext in ['.mp4', '.webm', '.mkv', '.avi']:
        media_type = 'video/mp4' if file_ext == '.mp4' else 'video/webm'
    else:
        media_type = 'audio/wav'
    
    return FileResponse(
        path=file_path,
        media_type=media_type,
        headers={"Accept-Ranges": "bytes"}
    )

@app.get("/download/{filename}")
async def download_file(filename: str):
    """Download extracted audio/video file"""
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Determine media type based on file extension
    file_ext = Path(filename).suffix.lower()
    if file_ext in ['.mp4', '.webm', '.mkv', '.avi']:
        media_type = 'video/mp4' if file_ext == '.mp4' else 'video/webm'
    else:
        media_type = 'audio/wav'
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type
    )

@app.post("/cleanup")
async def cleanup():
    """Clean up web_output folder"""
    try:
        if OUTPUT_DIR.exists():
            shutil.rmtree(OUTPUT_DIR)
            OUTPUT_DIR.mkdir(exist_ok=True)
        return {"status": "success", "message": "Output folder cleaned"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    import platform
    
    # Platform detection for startup message
    system = platform.system()
    if system == "Darwin":
        platform_info = "🍎 macOS"
    elif system == "Linux":
        platform_info = "🐧 Linux/Ubuntu"
    elif system == "Windows":
        platform_info = "🪟 Windows"
    else:
        platform_info = "🖥️ Unknown Platform"
    
    print(f"🎵 Starting StayTuned Web Interface on {platform_info}")
    print("📱 Open http://localhost:8000 in your browser")
    
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except KeyboardInterrupt:
        print("\n👋 StayTuned stopped")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        print("Try running: python3 install.py")