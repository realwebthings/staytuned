#!/usr/bin/env python3
"""
Automated video extraction and upload system
Monitors a redirect link, extracts video when available, uploads to S3
"""

import os
import time
import logging
import requests
import boto3
from pathlib import Path
from ai_extractor import AIAudioExtractor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VideoAutomation:
    def __init__(self, aws_access_key: str, aws_secret_key: str, s3_bucket: str, aws_region: str = 'us-east-1'):
        """Initialize automation with AWS credentials"""
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_key_id=aws_secret_key,
            region_name=aws_region
        )
        self.bucket = s3_bucket
        self.extractor = AIAudioExtractor()
        self.processed_urls = set()
        
    def check_redirect(self, url: str) -> str:
        """Check if URL redirects to YouTube and return final URL"""
        try:
            response = requests.head(url, allow_redirects=True, timeout=10)
            final_url = response.url
            
            if 'youtube.com' in final_url or 'youtu.be' in final_url:
                logger.info(f"Detected YouTube URL: {final_url}")
                return final_url
            return None
        except Exception as e:
            logger.error(f"Error checking redirect: {e}")
            return None
    
    def extract_video(self, youtube_url: str, extract_audio: bool = True) -> dict:
        """Extract video and/or audio from YouTube URL"""
        try:
            temp_dir = "./automation_temp"
            os.makedirs(temp_dir, exist_ok=True)
            
            # Download video (and optionally audio for AI processing)
            download_results = self.extractor.download_audio(
                youtube_url, 
                temp_dir, 
                download_video=True,
                download_audio=extract_audio
            )
            
            results = {'video': None, 'audio_tracks': []}
            
            # Process audio if requested
            if extract_audio and 'audio' in download_results:
                audio_file = download_results['audio']
                separated = self.extractor.separate_sources(audio_file, temp_dir)
                results['audio_tracks'] = list(separated.values())
                
                # Clean up temp audio
                if os.path.exists(audio_file):
                    os.unlink(audio_file)
            
            # Add video file
            if 'video' in download_results:
                results['video'] = download_results['video']
            
            return results
            
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            raise
    
    def upload_to_s3(self, file_path: str, s3_key: str = None) -> str:
        """Upload file to S3 and return public URL"""
        try:
            if not s3_key:
                s3_key = Path(file_path).name
            
            logger.info(f"Uploading {file_path} to S3...")
            self.s3_client.upload_file(
                file_path,
                self.bucket,
                s3_key,
                ExtraArgs={'ContentType': self._get_content_type(file_path)}
            )
            
            s3_url = f"https://{self.bucket}.s3.amazonaws.com/{s3_key}"
            logger.info(f"Uploaded: {s3_url}")
            return s3_url
            
        except Exception as e:
            logger.error(f"S3 upload failed: {e}")
            raise
    
    def _get_content_type(self, file_path: str) -> str:
        """Get content type based on file extension"""
        ext = Path(file_path).suffix.lower()
        types = {
            '.mp4': 'video/mp4',
            '.webm': 'video/webm',
            '.wav': 'audio/wav',
            '.mp3': 'audio/mpeg'
        }
        return types.get(ext, 'application/octet-stream')
    
    def cleanup_local_files(self, file_paths: list):
        """Delete local files after upload"""
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
                    logger.info(f"Deleted: {file_path}")
            except Exception as e:
                logger.error(f"Failed to delete {file_path}: {e}")
    
    def process_link(self, redirect_url: str, extract_audio: bool = True) -> dict:
        """Complete workflow: check redirect, extract, upload, cleanup"""
        # Step 1: Check if link redirects to YouTube
        youtube_url = self.check_redirect(redirect_url)
        if not youtube_url:
            logger.warning("URL does not redirect to YouTube")
            return None
        
        # Skip if already processed
        if youtube_url in self.processed_urls:
            logger.info("URL already processed, skipping")
            return None
        
        # Step 2: Extract video (and optionally audio)
        logger.info("Starting extraction...")
        extracted = self.extract_video(youtube_url, extract_audio)
        
        # Step 3: Upload to S3
        uploaded_urls = {'video': None, 'audio_tracks': []}
        all_files = []
        
        if extracted['video']:
            video_key = f"videos/{Path(extracted['video']).name}"
            uploaded_urls['video'] = self.upload_to_s3(extracted['video'], video_key)
            all_files.append(extracted['video'])
        
        for audio_file in extracted['audio_tracks']:
            audio_key = f"audio/{Path(audio_file).name}"
            url = self.upload_to_s3(audio_file, audio_key)
            uploaded_urls['audio_tracks'].append(url)
            all_files.append(audio_file)
        
        # Step 4: Cleanup local files
        self.cleanup_local_files(all_files)
        
        # Mark as processed
        self.processed_urls.add(youtube_url)
        
        return uploaded_urls
    
    def monitor_link(self, redirect_url: str, check_interval: int = 300, extract_audio: bool = True):
        """Continuously monitor a redirect link for new videos"""
        logger.info(f"Starting monitor for: {redirect_url}")
        logger.info(f"Check interval: {check_interval} seconds")
        
        while True:
            try:
                result = self.process_link(redirect_url, extract_audio)
                if result:
                    logger.info(f"Processing complete! Uploaded files:")
                    logger.info(f"Video: {result['video']}")
                    for i, audio_url in enumerate(result['audio_tracks'], 1):
                        logger.info(f"Audio {i}: {audio_url}")
                
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                logger.info("Monitor stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                time.sleep(check_interval)


if __name__ == "__main__":
    import sys
    
    # Configuration
    AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    S3_BUCKET = os.getenv('S3_BUCKET_NAME')
    
    if not all([AWS_ACCESS_KEY, AWS_SECRET_KEY, S3_BUCKET]):
        print("Error: Set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and S3_BUCKET_NAME environment variables")
        sys.exit(1)
    
    # Get redirect URL from command line
    if len(sys.argv) < 2:
        print("Usage: python3 automation.py <redirect_url> [--no-audio] [--interval 300]")
        print("\nExample:")
        print("  python3 automation.py https://example.com/video-link")
        print("  python3 automation.py https://example.com/video-link --no-audio")
        print("  python3 automation.py https://example.com/video-link --interval 600")
        sys.exit(1)
    
    redirect_url = sys.argv[1]
    extract_audio = '--no-audio' not in sys.argv
    
    # Get check interval
    check_interval = 300  # 5 minutes default
    if '--interval' in sys.argv:
        idx = sys.argv.index('--interval')
        if idx + 1 < len(sys.argv):
            check_interval = int(sys.argv[idx + 1])
    
    # Initialize and run
    automation = VideoAutomation(AWS_ACCESS_KEY, AWS_SECRET_KEY, S3_BUCKET)
    
    # One-time processing or continuous monitoring
    if '--monitor' in sys.argv:
        automation.monitor_link(redirect_url, check_interval, extract_audio)
    else:
        result = automation.process_link(redirect_url, extract_audio)
        if result:
            print("\n✅ Processing complete!")
            print(f"Video: {result['video']}")
            for i, audio_url in enumerate(result['audio_tracks'], 1):
                print(f"Audio track {i}: {audio_url}")
