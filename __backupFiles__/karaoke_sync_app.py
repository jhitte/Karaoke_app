import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import nemo.collections.asr as nemo_asr
import librosa
from pydub import AudioSegment
import logging
from pathlib import Path
import numpy as np

# Setup logging
log_dir = Path(r"D:\karaoke_app\logs")
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    filename=log_dir / "error.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="a"
)

class KaraokeSyncApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Karaoke Sync App")
        self.root.geometry("600x500")
        
        # Initialize variables
        self.audio_dir = tk.StringVar(value=r"D:\karaoke_app\audio_to_sync")
        self.lyrics_dir = tk.StringVar(value=r"D:\karaoke_app\lyrics")
        self.output_dir = tk.StringVar(value=r"D:\karaoke_app\output")
        self.file_pairs = []
        
        # GUI Elements
        tk.Label(root, text="Karaoke Sync App", font=("Arial", 16)).pack(pady=10)
        
        # Audio Folder
        tk.Label(root, text="Audio Folder:", font=("Arial", 10)).pack()
        tk.Entry(root, textvariable=self.audio_dir, width=50).pack()
        tk.Button(root, text="Browse Audio", command=self.browse_audio, bg="blue", fg="white").pack(pady=5)
        
        # Lyrics Folder
        tk.Label(root, text="Lyrics Folder:", font=("Arial", 10)).pack()
        tk.Entry(root, textvariable=self.lyrics_dir, width=50).pack()
        tk.Button(root, text="Browse Lyrics", command=self.browse_lyrics, bg="blue", fg="white").pack(pady=5)
        
        # Output Folder
        tk.Label(root, text="Output Folder:", font=("Arial", 10)).pack()
        tk.Entry(root, textvariable=self.output_dir, width=50).pack()
        tk.Button(root, text="Browse Output", command=self.browse_output, bg="blue", fg="white").pack(pady=5)
        
        # File Pair Confirmation
        tk.Button(root, text="Confirm File Pairs", command=self.show_file_pairs, bg="green", fg="white").pack(pady=10)
        
        # Progress Bar
        self.progress = ttk.Progressbar(root, length=400, mode="determinate")
        self.progress.pack(pady=10)
        
        # Start Processing Button
        tk.Button(root, text="Start Processing", command=self.start_processing, bg="green", fg="white").pack(pady=10)
        
        # Status Label
        self.status = tk.Label(root, text="", font=("Arial", 10))
        self.status.pack(pady=5)

    def browse_audio(self):
        folder = filedialog.askdirectory(initialdir=self.audio_dir.get())
        if folder:
            self.audio_dir.set(folder)

    def browse_lyrics(self):
        folder = filedialog.askdirectory(initialdir=self.lyrics_dir.get())
        if folder:
            self.lyrics_dir.set(folder)

    def browse_output(self):
        folder = filedialog.askdirectory(initialdir=self.output_dir.get())
        if folder:
            self.output_dir.set(folder)

    def get_file_pairs(self):
        audio_files = [f for f in os.listdir(self.audio_dir.get()) if f.endswith((".mp3", ".wav"))]
        lyrics_files = [f for f in os.listdir(self.lyrics_dir.get()) if f.endswith(".txt")]
        
        pairs = []
        for audio in audio_files:
            base_name = Path(audio).stem
            lyrics = f"{base_name}.txt"
            if lyrics in lyrics_files:
                pairs.append((audio, lyrics))
            else:
                logging.warning(f"No matching lyrics file for {audio}")
        
        for lyrics in lyrics_files:
            if not any(lyrics == pair[1] for pair in pairs):
                logging.warning(f"No matching audio file for {lyrics}")
        
        return pairs

    def show_file_pairs(self):
        self.file_pairs = self.get_file_pairs()
        if not self.file_pairs:
            messagebox.showerror("Error", "No matching audio and lyrics files found!")
            return
        
        # Create confirmation window
        confirm_window = tk.Toplevel(self.root)
        confirm_window.title("Confirm File Pairs")
        confirm_window.geometry("400x300")
        
        tk.Label(confirm_window, text="Confirm Audio-Lyrics Pairs", font=("Arial", 12)).pack(pady=10)
        
        listbox = tk.Listbox(confirm_window, width=60, height=10)
        for audio, lyrics in self.file_pairs:
            listbox.insert(tk.END, f"Audio: {audio} | Lyrics: {lyrics}")
        listbox.pack(pady=10)
        
        tk.Button(confirm_window, text="Confirm", command=confirm_window.destroy, bg="green", fg="white").pack(pady=5)

    def parse_metadata(self, filename):
        try:
            parts = Path(filename).stem.split("_", 1)
            if len(parts) == 2:
                artist = parts[0].replace("_", " ")
                title = parts[1].replace("_", " ")
                return artist, title
            return None, None
        except Exception as e:
            logging.error(f"Failed to parse metadata from {filename}: {e}")
            return None, None

    def format_time(self, time_sec):
        minutes = int(time_sec // 60)
        seconds = int(time_sec % 60)
        milliseconds = int((time_sec % 1) * 100)
        return f"[{minutes:02d}:{seconds:02d}.{milliseconds:02d}]"

    def map_lyrics_to_timestamps(self, lyrics_path, audio_path, word_timestamps):
        with open(lyrics_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        
        num_lines = len(lines)
        if num_lines == 0:
            logging.error(f"No lyrics lines in {lyrics_path}.")
            return [], []
        
        # Get word-level timestamps from NeMo
        timestamps = []
        for word in word_timestamps:
            if hasattr(word, 'start_time'):
                timestamps.append({"start": word.start_time, "end": getattr(word, 'end_time', word.start_time + 0.5)})
        
        # Fallback to linear interpolation if no timestamps
        if not timestamps:
            logging.warning(f"No word-level timestamps for {lyrics_path}. Using linear interpolation.")
        
        # Get audio duration with Librosa
        try:
            audio_duration, _ = librosa.get_duration(path=audio_path)
        except Exception as e:
            logging.error(f"Failed to get duration for {audio_path}: {e}")
            audio_duration = 300.0  # Fallback
        
        # Interpolate timestamps to match number of lyrics lines, starting at ~21s
        num_timestamps = len(timestamps)
        if num_timestamps == 0:
            logging.error(f"No valid timestamps for {lyrics_path}. Using interpolation.")
            first_line_time = 21.0
            step = (audio_duration - first_line_time) / max(num_lines - 1, 1)
            mapped_timestamps = [{"start": first_line_time + i * step, "end": first_line_time + (i + 1) * step} for i in range(num_lines)]
            return lines, mapped_timestamps
        
        # Filter timestamps with reasonable duration (>0.2s)
        filtered_timestamps = [t for t in timestamps if t["end"] - t["start"] >= 0.2]
        if not filtered_timestamps:
            filtered_timestamps = timestamps
        
        # Adjust to start at ~21s
        first_line_time = 21.0
        if num_timestamps < num_lines:
            # Interpolate over full duration, starting at 21s
            step = (audio_duration - first_line_time) / max(num_lines - 1, 1)
            mapped_timestamps = []
            for i in range(num_lines):
                start = first_line_time + i * step
                end = start + min(step, 2.0)  # Cap duration at 2s
                mapped_timestamps.append({"start": start, "end": end})
        elif num_timestamps > num_lines:
            # Downsample timestamps, starting at 21s
            indices = np.linspace(0, num_timestamps - 1, num_lines, dtype=int)
            mapped_timestamps = [filtered_timestamps[i] for i in indices]
            # Shift to start at ~21s
            if mapped_timestamps[0]["start"] < first_line_time:
                offset = first_line_time - mapped_timestamps[0]["start"]
                for t in mapped_timestamps:
                    t["start"] += offset
                    t["end"] += offset
        else:
            mapped_timestamps = filtered_timestamps
            # Shift to start at ~21s
            if mapped_timestamps[0]["start"] < first_line_time:
                offset = first_line_time - mapped_timestamps[0]["start"]
                for t in mapped_timestamps:
                    t["start"] += offset
                    t["end"] += offset
        
        return lines, mapped_timestamps

    def create_lrc(self, lyrics_path, audio_path, word_timestamps, artist, title):
        lrc_lines = []
        if artist:
            lrc_lines.append(f"[ar:{artist}]")
        if title:
            lrc_lines.append(f"[ti:{title}]")
            
        lines, timestamps = self.map_lyrics_to_timestamps(lyrics_path, audio_path, word_timestamps)
        if not lines or not timestamps:
            return ""
        
        for line, timestamp in zip(lines, timestamps):
            lrc_lines.append(f"{self.format_time(timestamp['start'])}{line}")
        
        return "\n".join(lrc_lines)

    def process_file(self, audio_file, lyrics_file, output_dir):
        try:
            audio_path = Path(self.audio_dir.get()) / audio_file
            lyrics_path = Path(self.lyrics_dir.get()) / lyrics_file
            output_path = Path(output_dir) / f"{Path(audio_file).stem}.lrc"
            
            # Skip if output already exists
            if output_path.exists():
                logging.info(f"Skipping {audio_file}: Output {output_path} already exists")
                return
            
            # Preprocess audio with PyDub
            audio = AudioSegment.from_file(audio_path)
            audio = audio.set_channels(1).set_frame_rate(16000).set_sample_width(2)  # Mono, 16kHz, 16-bit
            temp_audio = audio_path.with_suffix(".temp.wav")
            audio.export(temp_audio, format="wav")
            
            # Load NeMo model
            model = nemo_asr.models.ASRModel.from_pretrained("stt_en_fastconformer_transducer_large")
            
            # Transcribe with word-level timestamps
            hypotheses = model.transcribe([str(temp_audio)], batch_size=8, return_hypotheses=True, num_workers=0)
            word_timestamps = hypotheses[0].word_timestamps if hypotheses and hasattr(hypotheses[0], 'word_timestamps') else []
            
            # Clean up temp audio
            os.remove(temp_audio)
            
            # Parse metadata
            artist, title = self.parse_metadata(audio_file)
            
            # Create LRC
            lrc_content = self.create_lrc(lyrics_path, audio_path, word_timestamps, artist, title)
            if not lrc_content:
                logging.error(f"Failed to create LRC for {audio_file}.")
                return
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(lrc_content)
            
            logging.info(f"Successfully processed {audio_file} to {output_path}")
            
        except Exception as e:
            logging.error(f"Error processing {audio_file}: {e}")
            raise

    def start_processing(self):
        if not self.file_pairs:
            messagebox.showerror("Error", "Please confirm file pairs first!")
            return
        
        output_dir = self.output_dir.get()
        Path(output_dir).mkdir(exist_ok=True)
        
        self.progress["maximum"] = len(self.file_pairs)
        self.progress["value"] = 0
        
        for i, (audio, lyrics) in enumerate(self.file_pairs, 1):
            self.status.config(text=f"Processing {audio}...")
            self.root.update()
            self.process_file(audio, lyrics, output_dir)
            self.progress["value"] = i
            self.root.update()
        
        self.status.config(text="Processing complete!")
        messagebox.showinfo("Success", "All files processed. Check logs for details.")

if __name__ == "__main__":
    root = tk.Tk()
    app = KaraokeSyncApp(root)
    root.mainloop()