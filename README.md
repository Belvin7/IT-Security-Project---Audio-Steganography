# Audio & Image Steganalysis Scripts

## Overview
Python scripts developed for a cybersecurity research project investigating 
the detection of steganographic content hidden within audio and image files. 
The scripts in this repository automate data extraction from forensic analysis 
tools, supporting a team-wide investigation into steganography detection and 
attacker attribution.

## Repository Contents
- **Audio analysis scripts** — read and process output from tools such as 
  Sherlock and an MP3 file structure analyzer, extracting indicators of 
  embedded data (e.g. high-frequency distortion, signal irregularities) in 
  stego-MP3 files and writing results to a shared comparison dataset
- **Image analysis scripts** — extract and compare steganographic indicators 
  across image samples for cross-referencing with audio findings

## Project Background
These scripts were built as part of a larger team project that simulated 
**16 steganography attacks** across **8 devices** and **4 attacker profiles 
("Alices")**, each assigned a unique case index (e.g. `A1.1`). Stego-audio 
samples were generated and analyzed using **FFMPEG**, **SOX**, **PyTai**, 
**Sherlock**, and an **MP3 file structure analyzer**, with results consolidated 
into a shared Excel sheet to identify patterns and commonalities across samples.

Detection relied on spectrogram and metadata analysis, evaluated against three 
forensic criteria: detectability of the attack (**EDE**), attribution to number 
of attackers (**EAT**), and traceability to a specific attacker (**EDI**). The 
project also assessed how well hidden payloads survived real-world audio 
transformations such as recompression and format conversion.

## Outcome
The broader project identified consistent forensic signatures in manipulated 
audio — including high-frequency distortion and minor signal irregularities — 
demonstrating both the viability of audio as a covert communication channel 
and the practical limits of its concealment under structured forensic analysis.

## Tools & Technologies
`Python` · `FFMPEG` · `SOX` · `PyTai` · `Sherlock` · `MP3 File Structure Analyzer` · `Excel`
