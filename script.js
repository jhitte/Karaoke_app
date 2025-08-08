document.addEventListener('DOMContentLoaded', () => {
  const player = document.getElementById('player');
  const lyricsDiv = document.getElementById('lyrics');
  let lastWord = '';

  fetch('processed_audio/DoesToMe_sync.json')
    .then(res => {
      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
      return res.json();
    })
    .then(data => {
      console.log('Fetched sync data:', data);
      const fragments = data;
      if (!fragments || !fragments.length) {
        lyricsDiv.innerHTML = '<strong>No lyrics data available</strong>';
        return;
      }
      player.addEventListener('timeupdate', () => {
        const current = player.currentTime;
        console.log('Current time:', current);
        const activeWord = fragments.find(w => current >= w.start_time && current <= w.end_time);
        if (activeWord && activeWord.word !== lastWord) {
          lyricsDiv.innerHTML = `<strong>${activeWord.word}</strong>`;
          lastWord = activeWord.word;
        }
      });
      player.addEventListener('loadedmetadata', () => {
        console.log('Duration:', player.duration);
      });
    })
    .catch(error => {
      console.error('Error fetching sync data:', error);
      lyricsDiv.innerHTML = '<strong>Error loading lyrics</strong>';
    });
});