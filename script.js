document.addEventListener('DOMContentLoaded', () => {
  const player = document.getElementById('player');
  const lyricsDiv = document.getElementById('lyrics');
  fetch('processed_audio/DoesToMeVocals_sync.json')
    .then(res => res.json())
    .then(sync => {
      player.addEventListener('timeupdate', () => {
        const current = player.currentTime;
        const currentWord = sync.find(w => current >= w.start_time && current <= w.end_time);
        lyricsDiv.innerHTML = currentWord ? `<strong>${currentWord.word}</strong>` : '';
      });
    });
});