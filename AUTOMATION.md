# Video Automation System

Automatically monitor redirect links, extract videos from YouTube, and upload to AWS S3.

## Setup

### 1. Install AWS CLI and boto3
```bash
pip install boto3
```

### 2. Create AWS S3 Bucket
1. Go to AWS Console → S3
2. Create new bucket (e.g., `staytuned-videos`)
3. Enable public access if you want public URLs
4. Note your bucket name

### 3. Get AWS Credentials
1. Go to AWS Console → IAM → Users
2. Create new user with S3 access
3. Generate access keys
4. Save `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`

### 4. Set Environment Variables
```bash
export AWS_ACCESS_KEY_ID="your_access_key"
export AWS_SECRET_ACCESS_KEY="your_secret_key"
export S3_BUCKET_NAME="your-bucket-name"
```

Or create `.env` file:
```
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
S3_BUCKET_NAME=your-bucket-name
```

## Usage

### One-time Processing
Process a redirect link once:
```bash
python3 automation.py "https://example.com/video-link"
```

### Video Only (No Audio Extraction)
```bash
python3 automation.py "https://example.com/video-link" --no-audio
```

### Continuous Monitoring
Monitor link every 5 minutes (300 seconds):
```bash
python3 automation.py "https://example.com/video-link" --monitor
```

### Custom Check Interval
Check every 10 minutes (600 seconds):
```bash
python3 automation.py "https://example.com/video-link" --monitor --interval 600
```

## How It Works

1. **Check Redirect**: Follows the redirect link to detect YouTube URL
2. **Extract Video**: Downloads video (and optionally extracts audio with AI)
3. **Upload to S3**: Uploads all files to S3 bucket
4. **Cleanup**: Deletes local files after successful upload
5. **Repeat**: (If monitoring) Waits and checks again

## S3 Structure

Files are organized in S3:
```
your-bucket/
├── videos/
│   └── video_abc123.mp4
└── audio/
    ├── audio_abc123_vocals.wav
    ├── audio_abc123_drums.wav
    ├── audio_abc123_bass.wav
    ├── audio_abc123_other.wav
    └── audio_abc123_pure_instrumental.wav
```

## AWS Free Tier

AWS S3 Free Tier includes:
- 5 GB storage
- 20,000 GET requests
- 2,000 PUT requests
- Valid for 12 months

**Cost after free tier:** ~$0.023/GB/month

## Alternative: Firebase Storage

If you prefer Firebase (free tier: 5GB storage, 1GB/day downloads):

1. Install Firebase Admin SDK:
```bash
pip install firebase-admin
```

2. Download service account key from Firebase Console
3. Modify `automation.py` to use Firebase instead of S3

## Examples

### Example 1: Process single video with audio extraction
```bash
python3 automation.py "https://redirect.link/video1"
```

### Example 2: Monitor link, video only, check every hour
```bash
python3 automation.py "https://redirect.link/live" --monitor --no-audio --interval 3600
```

### Example 3: Run as background service
```bash
nohup python3 automation.py "https://redirect.link/live" --monitor > automation.log 2>&1 &
```

## Troubleshooting

**Error: AWS credentials not found**
- Set environment variables correctly
- Check IAM user has S3 permissions

**Error: Bucket not found**
- Verify bucket name is correct
- Check bucket region matches AWS_REGION

**Error: Access denied**
- Ensure IAM user has `s3:PutObject` permission
- Check bucket policy allows uploads

## Production Deployment

For production, run on a server:

1. **AWS EC2**: Run automation script 24/7
2. **Cron Job**: Schedule periodic checks
3. **Docker**: Containerize for easy deployment
4. **Lambda**: Trigger on schedule (for short videos only)

### Cron Example (check every hour)
```bash
0 * * * * cd /path/to/staytuned && /usr/bin/python3 automation.py "https://link" >> automation.log 2>&1
```
