document.getElementById('uploadForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append('file', document.getElementById('audioFile').files[0]);
    
    document.getElementById('progress').style.display = 'block';
    document.getElementById('results').innerHTML = '';
    
    try {
        const response = await fetch('/extract-file', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const result = await response.json();
            showResults(result);
        } else {
            throw new Error('Extraction failed');
        }
    } catch (error) {
        document.getElementById('results').innerHTML = '<p style="color: red;">Error: ' + error.message + '</p>';
    } finally {
        document.getElementById('progress').style.display = 'none';
    }
});

document.getElementById('urlForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const url = document.getElementById('youtubeUrl').value;
    
    document.getElementById('progress').style.display = 'block';
    document.getElementById('results').innerHTML = '';
    
    try {
        const response = await fetch('/extract-url', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({url: url})
        });
        
        if (response.ok) {
            const result = await response.json();
            showResults(result);
        } else {
            throw new Error('Extraction failed');
        }
    } catch (error) {
        document.getElementById('results').innerHTML = '<p style="color: red;">Error: ' + error.message + '</p>';
    } finally {
        document.getElementById('progress').style.display = 'none';
    }
});

function showResults(result) {
    let html = '<h3>✅ Extraction Complete!</h3>';
    
    // Audio players section
    html += '<div class="audio-player">';
    html += '<h4>🎵 Stream & Preview</h4>';
    html += '<div class="audio-controls">';
    html += '<button class="play-all-btn" onclick="playAll()">▶️ Play All</button>';
    html += '<button class="play-all-btn" onclick="stopAll()">⏹️ Stop All</button>';
    html += '</div>';
    
    const trackLabels = {
        'vocals': '🎤 Vocals Only',
        'drums': '🥁 Drums Only', 
        'bass': '🎸 Bass Only',
        'other': '🎹 Other Instruments',
        'pure_instrumental': '🎼 Pure Instrumental'
    };
    
    for (const file of result.files) {
        const trackType = Object.keys(trackLabels).find(key => file.includes(key)) || 'unknown';
        const label = trackLabels[trackType] || file;
        
        html += `<div class="track-label">${label}</div>`;
        html += `<audio controls preload="metadata" id="audio_${trackType}">`;
        html += `<source src="/stream/${file}" type="audio/wav">`;
        html += 'Your browser does not support the audio element.';
        html += '</audio>';
    }
    html += '</div>';
    
    // Mixer section
    html += '<div class="mixer-section">';
    html += '<h4>🎛️ Audio Mixer</h4>';
    html += '<div class="mixer-control">';
    html += '<label>🎤 Vocals:</label>';
    html += '<input type="range" id="vocals-volume" min="0" max="200" value="100" oninput="updateMixer()">';
    html += '<span id="vocals-value">100%</span>';
    html += '</div>';
    html += '<div class="mixer-control">';
    html += '<label>🥁 Drums:</label>';
    html += '<input type="range" id="drums-volume" min="0" max="200" value="100" oninput="updateMixer()">';
    html += '<span id="drums-value">100%</span>';
    html += '</div>';
    html += '<div class="mixer-control">';
    html += '<label>🎸 Bass:</label>';
    html += '<input type="range" id="bass-volume" min="0" max="200" value="100" oninput="updateMixer()">';
    html += '<span id="bass-value">100%</span>';
    html += '</div>';
    html += '<div class="mixer-control">';
    html += '<label>🎹 Other:</label>';
    html += '<input type="range" id="other-volume" min="0" max="200" value="100" oninput="updateMixer()">';
    html += '<span id="other-value">100%</span>';
    html += '</div>';
    html += '<div class="mixer-buttons">';
    html += '<button class="mixer-btn" onclick="resetMixer()">Reset</button>';
    html += '<button class="mixer-btn" onclick="muteVocals()">Mute Vocals</button>';
    html += '<button class="mixer-btn" onclick="soloInstruments()">Solo Instruments</button>';
    html += '</div>';
    html += '</div>';
    
    // Download section
    html += '<h4>💾 Download Files</h4>';
    for (const file of result.files) {
        html += `<a href="/download/${file}" class="download-link">${file}</a>`;
    }
    
    document.getElementById('results').innerHTML = html;
}

function playAll() {
    const audios = document.querySelectorAll('audio');
    audios.forEach(audio => {
        audio.currentTime = 0;
        audio.play();
    });
}

function stopAll() {
    const audios = document.querySelectorAll('audio');
    audios.forEach(audio => {
        audio.pause();
        audio.currentTime = 0;
    });
}

function updateMixer() {
    const tracks = ['vocals', 'drums', 'bass', 'other'];
    tracks.forEach(track => {
        const slider = document.getElementById(`${track}-volume`);
        const valueSpan = document.getElementById(`${track}-value`);
        const audio = document.getElementById(`audio_${track}`);
        
        if (slider && valueSpan && audio) {
            const volume = slider.value / 100;
            valueSpan.textContent = slider.value + '%';
            audio.volume = Math.min(volume, 1.0);
        }
    });
}

function resetMixer() {
    const tracks = ['vocals', 'drums', 'bass', 'other'];
    tracks.forEach(track => {
        const slider = document.getElementById(`${track}-volume`);
        if (slider) {
            slider.value = 100;
        }
    });
    updateMixer();
}

function muteVocals() {
    const vocalsSlider = document.getElementById('vocals-volume');
    if (vocalsSlider) {
        vocalsSlider.value = 0;
        updateMixer();
    }
}

function soloInstruments() {
    document.getElementById('vocals-volume').value = 0;
    document.getElementById('drums-volume').value = 100;
    document.getElementById('bass-volume').value = 100;
    document.getElementById('other-volume').value = 100;
    updateMixer();
}