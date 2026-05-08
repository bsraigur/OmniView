# 👁️ OmniView

**OmniView** is a powerful, Python-based multi-video player and sorting tool built with PyQt6. Designed for researchers, data annotators, and security professionals, OmniView allows users to watch, synchronize, and rapidly sort through massive queues of video files using up to 10 simultaneous screens.

Originally built to manage and review CCTV and detection datasets on Ubuntu, it includes native workarounds for common Linux display server bugs, making it a robust choice for desktop Linux environments.

## ✨ Features
* **Multi-Screen Grid:** View anywhere from 1 to 10 videos at the exact same time in a clean, responsive grid layout.
* **Synchronized Controls:** Play, pause, and seek (`+3s` / `-3s`) across all active video screens simultaneously using global hotkeys.
* **Rapid Sorting:** Quickly move videos to a `_save_` folder or send them to a `_delete_` trash folder without ever leaving the interface.
* **Pattern-Based Saving:** Automatically create and sort videos into dynamically named folders by extracting specific parts of the filename (e.g., separating by `_` or `-`).
* **Variable Playback Speed:** Speed up your review process from `1.0x` up to `4.0x`.
* **Wayland-Proof:** Bypasses the infamous Ubuntu Wayland "black screen" Qt bug by forcing the X11 (`xcb`) display server natively in the code.

---

## 🛠️ Installation

OmniView uses **PyQt6**, which conveniently bundles its own FFmpeg decoders. This means you generally do not need to install complex system-level GStreamer plugins to get started!

**1. Clone the repository:**
```bash
git clone [https://github.com/YOUR-USERNAME/OmniView.git](https://github.com/YOUR-USERNAME/OmniView.git)
cd OmniView
