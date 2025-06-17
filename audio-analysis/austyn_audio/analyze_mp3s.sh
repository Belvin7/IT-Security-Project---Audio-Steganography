#!/bin/bash

# Input files
cover="austyn_noise.mp3"
stegos=("stego_aa.mp3" "stego_ab.mp3" "stego_ex.mp3")

# Output directories
mkdir -p spectrograms stats diff_results noise_profiles cleaned wavs

# 1. Spectrograms
sox "$cover" -n spectrogram -o "spectrograms/${cover%.mp3}_spec.png"
for file in "${stegos[@]}"; do
    sox "$file" -n spectrogram -o "spectrograms/${file%.mp3}_spec.png"
done

# 2. Flat factor (generate from square wave reference)
echo -e "\n[Flat Factor Analysis of Reference Signal]"
sox -n -p synth 10 square 1 norm -3 | sox - -n stats

# 3. Min/Max Amplitude and Delta for each file
echo -e "\n[Amplitude Stats]"
files=("$cover" "${stegos[@]}")
for f in "${files[@]}"; do
    echo -e "\n--- $f ---"
    sox "$f" -n stats 2>&1 | grep -E 'Maximum amplitude|Minimum amplitude|DC offset'
done

# 4. Noise Profile + Noise Reduction
for file in "${stegos[@]}"; do
    base=${file%.mp3}
    sox "$file" "noise_profiles/${base}_noise.mp3" trim 0 0.9
    sox "noise_profiles/${base}_noise.mp3" -n noiseprof "noise_profiles/${base}.prof"
    sox "$file" "cleaned/${base}_clean.mp3" noisered "noise_profiles/${base}.prof" 0.21
done

# 5. Spectrogram Differences
for file in "${stegos[@]}"; do
    base=${file%.mp3}
    sox -m -v 1 "$cover" -v -1 "$file" -n spectrogram -o "diff_results/${base}_diff.png"
done

# 6. Full SoX Stats
echo -e "\n[Full SoX Stats]"
for f in "$cover" "${stegos[@]}"; do
    echo -e "\n--- $f ---"
    sox "$f" -n stats
done

# 7. Frequency Range Analysis (via Python with Average Frequency)
echo -e "\n[Frequency Range Analysis]"
PYTHON_SCRIPT=$(cat << 'EOF'
import numpy as np
import scipy.io.wavfile as wav
import os
import sys

def analyze_freq_range(filename):
    sr, data = wav.read(filename)
    if data.ndim > 1:
        data = data.mean(axis=1)

    fft_spectrum = np.fft.rfft(data)
    freq = np.fft.rfftfreq(len(data), d=1/sr)
    magnitude = np.abs(fft_spectrum)

    threshold = np.max(magnitude) * 0.001
    active_freqs = freq[magnitude > threshold]
    active_mags = magnitude[magnitude > threshold]

    if len(active_freqs) > 0:
        min_f = active_freqs.min()
        max_f = active_freqs.max()
        avg_f = np.sum(active_freqs * active_mags) / np.sum(active_mags)
    else:
        min_f = max_f = avg_f = 0

    print(f"{os.path.basename(filename)}: {int(min_f)} Hz to {int(max_f)} Hz | Avg: {int(avg_f)} Hz")

if __name__ == "__main__":
    for fname in sys.argv[1:]:
        analyze_freq_range(fname)
EOF
)

# Write Python code to file
echo "$PYTHON_SCRIPT" > freq_range.py

# Convert MP3s to WAV and analyze
for f in "$cover" "${stegos[@]}"; do
    base=${f%.mp3}
    wavfile="wavs/${base}.wav"
    ffmpeg -y -i "$f" -ac 1 -ar 44100 "$wavfile" > /dev/null 2>&1
    python3 freq_range.py "$wavfile"
done

# Cleanup
rm freq_range.py

# Done
echo -e "\n✅ Analysis complete. Check:"
echo "- Spectrograms: spectrograms/"
echo "- Spectrogram Diffs: diff_results/"
echo "- Noise-reduced versions: cleaned/"
echo "- Flat factor (visual): from square wave"
echo "- Frequency ranges + average: printed above"
