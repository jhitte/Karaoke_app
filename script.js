let lyricsData = {};
let timeKeys = [];
let lyricsLines = [];
let lastDisplayedTime = null;
const TIMESTAMP_OFFSET = -5.0; // Calibrated for ~5s delay in MP3

function loadSong(file) {
  const audio = document.getElementById('audioPlayer');
  const lyricsDiv = document.getElementById('lyrics');
  console.log("Loading song:", file);
  audio.src = file;
  lyricsDiv.textContent = 'Loading lyrics...';

  const lrcMap = {
    'heart_all_i_wanna_do_is_make_love_to_you.mp3': 'heart_all_i_wanna_do_is_make_love_to_you.lrc',
    'does_to_me.mp3': 'does_to_me.lrc'
  };

  const lrcFile = lrcMap[file];
  if (lrcFile) {
    fetch(lrcFile)
      .then(response => {
        if (!response.ok) throw new Error(`Failed to load ${lrcFile}`);
        return response.text();
      })
      .then(lrc => {
        parseLRC(lrc);
        audio.play().catch(e => {
          console.error("Playback error:", e);
          lyricsDiv.textContent = 'Error playing audio.';
        });
      })
      .catch(error => {
        console.error("Error loading lyrics:", error);
        lyricsData = {};
        timeKeys = [];
        lyricsLines = [];
        lyricsDiv.textContent = 'Lyrics not available.';
      });
  } else {
    lyricsData = {};
    timeKeys = [];
    lyricsLines = [];
    lyricsDiv.textContent = 'Lyrics not available.';
  }
}

function parseLRC(lrcText) {
  const lines = lrcText.split('\n');
  lyricsData = {};
  lyricsLines = [];
  lines.forEach(line => {
    const match = line.match(/\[(\d+):(\d+\.\d+)\](.*)/);
    if (match) {
      const minutes = parseInt(match[1]);
      const seconds = parseFloat(match[2]);
      const time = minutes * 60 + seconds;
      lyricsData[time] = match[3].trim();
      lyricsLines.push({ time, text: match[3].trim() });
      console.log(`Parsed [${match[1]}:${match[2]}] -> ${time}s: ${match[3].trim()}`);
    }
  });
  timeKeys = lyricsLines.map(l => l.time).sort((a, b) => a - b);
  if (timeKeys.length) {
    console.log(`LRC parsed, timestamps: ${timeKeys.length}, first: ${timeKeys[0]}`);
  } else {
    console.log('No valid timestamps parsed from LRC');
  }
}

function updateLyrics() {
  const lyricsDiv = document.getElementById('lyrics');
  const currentTime = audio.currentTime + TIMESTAMP_OFFSET;

  if (!timeKeys.length) {
    console.log(`Current time: ${currentTime.toFixed(2)}s, Lyrics not yet loaded`);
    return;
  }

  let closestIndex = -1;
  for (let i = timeKeys.length - 1; i >= 0; i--) {
    if (timeKeys[i] <= currentTime) {
      closestIndex = i;
      break;
    }
  }

  if (closestIndex !== -1 && timeKeys[closestIndex] !== lastDisplayedTime) {
    lastDisplayedTime = timeKeys[closestIndex];
    let start = Math.max(0, closestIndex - 2);
    let end = Math.min(lyricsLines.length, closestIndex + 3);
    let html = '';
    for (let j = start; j < end; j++) {
      const isCurrent = j === closestIndex;
      html += `<p class="lyrics-line ${isCurrent ? 'current-line' : ''}">${lyricsLines[j].text}</p>`;
    }
    lyricsDiv.innerHTML = html;
    const currentElem = lyricsDiv.querySelector('.current-line');
    if (currentElem) {
      currentElem.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    console.log(`Current time: ${currentTime.toFixed(2)}s, Displaying lyric at ${timeKeys[closestIndex]}s: ${lyricsLines[closestIndex].text}`);
  } else if (closestIndex === -1) {
    console.log(`Current time: ${currentTime.toFixed(2)}s, Before first lyric at ${timeKeys[0]}s`);
  } else {
    console.log(`Current time: ${currentTime.toFixed(2)}s, Holding last lyric at ${lastDisplayedTime}s`);
  }
}

const audio = document.getElementById('audioPlayer');
audio.addEventListener('timeupdate', updateLyrics);
audio.addEventListener('error', () => {
  document.getElementById('lyrics').textContent = 'Error loading audio.';
});