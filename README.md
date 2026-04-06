# 📚 BookGyaan AI Video Generator 🎬

> Automated AI-powered Hindi book summary video creation for YouTube

**Channel:** [@bookgyaan24-c1n](https://youtube.com/@bookgyaan24-c1n)

---

## ✨ Features

- 🤖 **AI Script Generation** — Gemini/GPT-4o creates engaging Hindi book summaries
- 🔊 **Hindi Text-to-Speech** — Natural Hindi narration via Edge-TTS (FREE)
- 🖼️ **AI Image Generation** — DALL-E 3 / Pexels / Placeholder visuals
- 🎬 **Auto Video Composition** — MoviePy assembles video with Ken Burns effect
- 📝 **Auto Subtitles** — SRT generation with proper Hindi text timing
- 🖼️ **Thumbnail Generator** — Eye-catching thumbnails with BookGyaan branding
- 📤 **YouTube Upload** — Direct upload via YouTube Data API v3
- 🔄 **Resume Support** — Pick up where you left off if something fails

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up API Keys

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your API keys
# At minimum, you need a Gemini API key (FREE)
```

**Get your FREE Gemini API key:** [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey)

### 3. Generate Your First Video

```bash
# Quick test with placeholders (no API key needed for images)
python main.py --book "Atomic Habits" --author "James Clear" --skip-images

# Full generation with AI images
python main.py --book "Atomic Habits" --author "James Clear"

# With review step (pause after script generation)
python main.py --book "Atomic Habits" --author "James Clear" --review
```

---

## 📖 Usage

```
python main.py --book "BOOK NAME" --author "AUTHOR" [options]

Required:
  --book          Book name
  --author        Author name

Options:
  --scenes N      Number of scenes (default: 15, for ~10 min video)
  --voice         Narrator voice: "male" or "female" (default: female)
  --upload        Upload to YouTube after rendering
  --privacy       YouTube privacy: public/private/unlisted (default: unlisted)
  --dry-run       Only generate script, don't render video
  --skip-images   Use placeholder images (no API needed)
  --review        Pause after script for manual review
  --music PATH    Path to background music MP3
  --resume-from   Resume from: script/audio/images/video
```

### Examples

```bash
# Just generate the script (preview mode)
python main.py --book "Rich Dad Poor Dad" --author "Robert Kiyosaki" --dry-run

# Male narrator with 12 scenes
python main.py --book "Ikigai" --author "Héctor García" --voice male --scenes 12

# Generate and auto-upload as unlisted
python main.py --book "The Psychology of Money" --author "Morgan Housel" --upload

# Resume video rendering after fixing images
python main.py --book "Atomic Habits" --author "James Clear" --resume-from video
```

---

## 📁 Project Structure

```
HRMX/
├── config/
│   └── settings.py              # All configuration & prompts
├── modules/
│   ├── script_generator.py      # LLM book summary script
│   ├── tts_engine.py            # Hindi text-to-speech
│   ├── image_generator.py       # AI image generation
│   ├── video_composer.py        # MoviePy video assembly
│   ├── subtitle_generator.py    # SRT subtitle creation
│   ├── thumbnail_generator.py   # YouTube thumbnail
│   └── youtube_uploader.py      # YouTube API upload
├── assets/
│   ├── fonts/                   # Hindi fonts
│   ├── music/                   # Background music (royalty-free)
│   ├── templates/               # Thumbnail templates
│   └── intro_outro/             # Channel intro/outro
├── output/                      # Generated videos
├── temp/                        # Working files (cached)
├── main.py                      # 🚀 Main entry point
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🔑 API Keys Setup

| Service | Cost | Purpose | Get Key |
|---------|------|---------|---------|
| **Google Gemini** | FREE | Script generation | [aistudio.google.com](https://aistudio.google.com/apikey) |
| **Edge-TTS** | FREE | Hindi speech | No key needed |
| **Pexels** | FREE | Stock images | [pexels.com/api](https://www.pexels.com/api/) |
| **OpenAI** | Paid | Better scripts + DALL-E images | [platform.openai.com](https://platform.openai.com/api-keys) |
| **YouTube API** | FREE | Video upload | [console.cloud.google.com](https://console.cloud.google.com) |

### YouTube Upload Setup (Optional)

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Enable **YouTube Data API v3**
4. Create **OAuth 2.0 Client ID** (Desktop Application)
5. Download the JSON → save as `client_secrets.json` in project root
6. First run will open browser for authorization

---

## 💡 Tips

- **Start with `--dry-run`** to preview the script before rendering
- **Use `--review`** to review and edit the script manually
- **Use `--skip-images`** for quick testing without image API costs
- **Add background music** in `assets/music/` — the first MP3 found will be used
- **Resume failed jobs** with `--resume-from` — cached data is saved in `temp/`
- **Edit scripts** — after `--review`, edit `temp/<book>/script.json` and continue

---

## 📋 Pipeline Flow

```
📖 Book Name → 🤖 Script → 🔊 Audio → 🖼️ Images → 🎬 Video → 📤 YouTube
              (Gemini)   (Edge-TTS)  (DALL-E)   (MoviePy)  (API v3)
```

Each step is cached, so if the pipeline fails at step 4, you can resume from step 4 without re-doing steps 1-3.

---

## 📜 License

This project is for personal use with the BookGyaan YouTube channel.

Made with ❤️ for 📚 BookGyaan
