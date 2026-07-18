# Audio Steganography Detection & Forensic Analysis

## Overview
A cybersecurity research project investigating the detection of steganographic 
content hidden within MP3 audio files. The project approaches the problem from 
both sides of the conflict — as an attacker embedding covert data, and as a 
forensic analyst working to detect and attribute it.

## Project Description
The project simulated **16 distinct steganography attacks** across **8 devices** 
and **4 attacker profiles ("Alices")**, each assigned a unique case index (e.g. 
`A1.1`). Stego-audio samples were generated and analyzed using **FFMPEG**, 
**SOX**, **PyTai**, **Sherlock**, and an **MP3 file structure analyzer**, with 
tool output automated via **Python scripts** into a shared Excel-based 
comparison sheet used to identify patterns and commonalities across samples.

Detection relied on **spectrogram and metadata analysis** to surface embedding 
artifacts, including high-frequency distortions and minor signal irregularities. 
Performance was evaluated across three forensic criteria:
- **EDE** — detectability of the attack
- **EAT** — attribution to number of attackers
- **EDI** — traceability to a specific attacker

The study also assessed payload robustness under real-world audio 
transformations such as recompression and format conversion, testing how well 
hidden data survives common processing pipelines.

## Tools & Technologies
`Python` · `FFMPEG` · `SOX` · `PyTai` · `Sherlock` · `MP3 File Structure Analyzer` · `Excel`

## Outcome
The project identified consistent forensic signatures in manipulated audio 
(high-frequency distortion, signal irregularities), demonstrating both the 
viability of audio as a covert communication channel and the practical limits 
of its concealment against structured forensic analysis.



