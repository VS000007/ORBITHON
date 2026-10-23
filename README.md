# 🌕 ORBITHON — Cosmic Crew: Chandrayaan-3 Lunar Topography AI

> **Team Cosmic Crew**  
> Autonomous Lunar Crater Detection & Safe Landing Reconnaissance System for Chandrayaan-3.

---

## 🚀 Overview

ORBITHON combines state-of-the-art AI crater topography detection with a cinematic, photorealistic 3D interactive lunar mission experience.

### Key Architecture:

1. **Stage 1 — Cosmic Crew Starting Portal (`intro.html`)**:
   - Doppelganger entrance animation featuring Team Cosmic Crew branding, logo, and artwork.
   - 3-second animated mission countdown with progress indicator.
2. **Stage 2 — Lunar Crater Landing Page (`lunar-landing/`)**:
   - Photorealistic 3D rotating Moon built with Three.js and real LRO (Lunar Reconnaissance Orbiter) surface textures.
   - Interactive orbit rotation controls, crater coordinates, and descent resolution HUD.
   - Seamless transition into the live detection suite.
3. **Stage 3 — ISRO Crater AI Detector (`app.py` & Live Cloud)**:
   - **Live Hosted Application**: [https://crater-scanner-8tvxwfgihwbljakvpxwb9r.streamlit.app/](https://crater-scanner-8tvxwfgihwbljakvpxwb9r.streamlit.app/)
   - Integrated directly into the landing page via an interactive high-performance embedded AI console with full-screen expansion.

---

## 🛠️ Quick Start

### 1. Run the Lunar Landing Page & Intro
Open `lunar-landing/index.html` or start a local server:
```bash
python -m http.server 3000 --directory lunar-landing
```
Visit: `http://localhost:3000/`

### 2. Access or Run the Crater Detection Suite
- **Live Cloud Deployment**: [https://crater-scanner-8tvxwfgihwbljakvpxwb9r.streamlit.app/](https://crater-scanner-8tvxwfgihwbljakvpxwb9r.streamlit.app/)
- **Local Development**:
```bash
pip install streamlit ultralytics pillow
streamlit run app.py
```
Visit: `http://localhost:8501/`

---

## 🔄 Automatic GitHub Sync

To automatically sync any local changes to this GitHub repository:
- **One-click**: Double-click `sync_github.bat`
- **Continuous auto-sync daemon**: Run `python auto_sync.py`
- **GitHub Pages CI/CD**: On every push to `main`, `.github/workflows/deploy.yml` automatically updates and deploys the landing page to GitHub Pages.

---

© 2026 Team Cosmic Crew. Built for Chandrayaan lunar reconnaissance.
