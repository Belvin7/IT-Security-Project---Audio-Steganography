#!/bin/bash

# Paths to files
COVER="austyn_noise.mp3"
STEGO="stego_aa.mp3"
NOISE_PROFILE="noise.prof"

# Convert to WAV
sox "$COVER" cover.wav
sox "$STEGO" stego.wav

# Extract Noise Profile from Cover
sox cover.wav -n noiseprof "$NOISE_PROFILE"

# Apply Noise Profile to both
sox cover.wav cover_denoised.wav noisered "$NOISE_PROFILE" 0.3
sox stego.wav stego_denoised.wav noisered "$NOISE_PROFILE" 0.3

# Generate Spectrograms
sox cover.wav -n spectrogram -o spectrogram_cover.png
sox stego.wav -n spectrogram -o spectrogram_stego.png

# Generate Spectrogram Difference via Python
python3 <<EOF
import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
import matplotlib

matplotlib.use('Agg')

def load_mono(path):
    rate, data = wavfile.read(path)
    if len(data.shape) > 1:
        data = data.mean(axis=1)
    return rate, data

_, cover = load_mono("cover.wav")
_, stego = load_mono("stego.wav")

# Spectral Diff
spec_cover = np.abs(np.fft.fft(cover))
spec_stego = np.abs(np.fft.fft(stego))
diff = np.abs(spec_cover - spec_stego)

plt.figure(figsize=(10, 4))
plt.plot(diff[:len(diff)//2])
plt.title("Spectrogram Difference")
plt.savefig("spectrogram_diff.png")
EOF

# Calculate PSNR and SNR via Python
python3 <<EOF
import numpy as np
from scipy.io import wavfile

def snr_psnr(original, modified):
    noise = original - modified
    noise_power = np.mean(noise**2)
    signal_power = np.mean(original**2)
    snr = 10 * np.log10(signal_power / noise_power)
    psnr = 10 * np.log10(np.max(original)**2 / noise_power)
    return snr, psnr

_, cover = wavfile.read("cover.wav")
_, stego = wavfile.read("stego.wav")

if cover.ndim > 1:
    cover = cover.mean(axis=1)
if stego.ndim > 1:
    stego = stego.mean(axis=1)

snr, psnr = snr_psnr(cover, stego)

with open("snr_psnr.txt", "w") as f:
    f.write(f"SNR: {snr:.2f} dB\\nPSNR: {psnr:.2f} dB\\n")
EOF

# Get SOX Stats
sox cover.wav -n stat 2> cover_stats.txt
sox stego.wav -n stat 2> stego_stats.txt

echo "✅ Analysis complete."
echo "Check:"
echo "- Spectrograms: spectrogram_*.png"
echo "- Spectrogram Diff: spectrogram_diff.png"
echo "- SNR/PSNR: snr_psnr.txt"
echo "- Sox stats: cover_stats.txt, stego_stats.txt"
