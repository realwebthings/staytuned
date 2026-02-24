# Fix YouTube "Sign in to confirm you're not a bot" Error

## macOS Keychain Prompt Issue

If you see a keychain login prompt, it's because yt-dlp needs to decrypt Chrome cookies.

### Option A: Allow Keychain Access (Easiest)
1. Enter your Mac password when prompted
2. Click "Always Allow" to avoid future prompts
3. Download will continue automatically

### Option B: Manual Cookie Export (Recommended - No Keychain)

**IMPORTANT: Must use Netscape format!**

1. Install Chrome extension: [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
2. Go to YouTube.com (logged in)
3. Click extension → **Export in Netscape format** (NOT JSON!)
4. Save as `youtube_cookies.txt` in project folder
5. Restart the app - it will auto-detect the cookie file

**Alternative extension (easier):** [cookies.txt](https://chrome.google.com/webstore/detail/cookiestxt/njabckikapfpffapmjgojcnbfjonfjfg) - exports in correct format by default

## Alternative Browsers

If you use a different browser, change this line in `ai_extractor.py`:

```python
'cookiesfrombrowser': ('chrome',),  # Change to your browser
```

**Supported browsers:**
- `'chrome'` - Google Chrome
- `'firefox'` - Mozilla Firefox
- `'safari'` - Safari (macOS)
- `'edge'` - Microsoft Edge
- `'brave'` - Brave Browser

## Manual Cookie Export (If automatic doesn't work)

### Option 1: Export cookies.txt

1. Install browser extension:
   - Chrome: [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
   - Firefox: [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)

2. Go to YouTube.com and login

3. Click extension icon → Export cookies

4. Save as `youtube_cookies.txt` in project folder

5. Update `ai_extractor.py`:
```python
audio_ydl_opts = {
    'cookiefile': 'youtube_cookies.txt',  # Add this line
    # ... rest of options
}
```

### Option 2: Use Different Browser Profile

```python
'cookiesfrombrowser': ('chrome', 'Profile 1'),  # Specify profile
```

## Troubleshooting

**Error: "Could not find Chrome cookies"**
- Make sure Chrome is installed
- Try logging into YouTube in Chrome first
- Try different browser: `'cookiesfrombrowser': ('firefox',)`

**Error: "No cookies found"**
- Close and reopen Chrome
- Clear Chrome cache and login to YouTube again
- Use manual cookie export method

**Still not working?**
- Update yt-dlp: `pip install -U yt-dlp`
- Try incognito/private browsing in Chrome, then export cookies

## Why This Happens

YouTube uses bot detection to prevent automated downloads. Using browser cookies makes yt-dlp appear as a regular browser session, bypassing the bot check.
