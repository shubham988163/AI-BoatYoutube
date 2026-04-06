"""
BookGyaan AI Video Generator — Configuration
=============================================
All settings, API keys, and constants.
Keys are loaded from environment variables or a .env file.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

# ─── Project Paths ───────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"
ASSETS_DIR = BASE_DIR / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
MUSIC_DIR = ASSETS_DIR / "music"
TEMPLATES_DIR = ASSETS_DIR / "templates"
INTRO_OUTRO_DIR = ASSETS_DIR / "intro_outro"
TEMP_DIR = BASE_DIR / "temp"

# Create directories if they don't exist
for d in [OUTPUT_DIR, ASSETS_DIR, FONTS_DIR, MUSIC_DIR, TEMPLATES_DIR, INTRO_OUTRO_DIR, TEMP_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ─── API Keys ────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")

# ─── LLM Settings ────────────────────────────────────────────────────────────
# Options: "gemini" or "openai"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")
GEMINI_MODEL = "gemini-2.0-flash"
OPENAI_MODEL = "gpt-4o"

# ─── TTS Settings ────────────────────────────────────────────────────────────
# Hindi voices available in Edge-TTS:
#   Female: "hi-IN-SwaraNeural"
#   Male:   "hi-IN-MadhurNeural"
TTS_VOICE = os.getenv("TTS_VOICE", "hi-IN-SwaraNeural")
TTS_RATE = os.getenv("TTS_RATE", "+0%")       # Speed: "-10%", "+0%", "+10%"
TTS_PITCH = os.getenv("TTS_PITCH", "+0Hz")     # Pitch adjustment

# ─── Image Generation Settings ───────────────────────────────────────────────
# Options: "dalle", "pexels" (free stock images)
IMAGE_PROVIDER = os.getenv("IMAGE_PROVIDER", "dalle")
IMAGE_WIDTH = 1920
IMAGE_HEIGHT = 1080
DALLE_MODEL = "dall-e-3"
DALLE_QUALITY = "standard"  # "standard" or "hd"

# ─── Video Settings ──────────────────────────────────────────────────────────
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
VIDEO_FPS = 30
VIDEO_CODEC = "libx264"
AUDIO_CODEC = "aac"
AUDIO_BITRATE = "192k"

# Transition and effects
CROSSFADE_DURATION = 0.8       # seconds of crossfade between scenes
KEN_BURNS_ZOOM = 1.08          # subtle zoom factor (1.0 = no zoom)
BACKGROUND_MUSIC_VOLUME = 0.08 # volume for background music (0.0 - 1.0)

# ─── Subtitle Settings ───────────────────────────────────────────────────────
SUBTITLE_FONT_SIZE = 42
SUBTITLE_FONT_COLOR = "white"
SUBTITLE_BG_COLOR = (0, 0, 0, 180)  # semi-transparent black
SUBTITLE_POSITION = ("center", "bottom")
SUBTITLE_FONT_NAME = "NotoSansDevanagari-Bold"  # Hindi font

# ─── Thumbnail Settings ──────────────────────────────────────────────────────
THUMBNAIL_WIDTH = 1280
THUMBNAIL_HEIGHT = 720
THUMBNAIL_FONT_SIZE = 72
THUMBNAIL_ACCENT_COLOR = (255, 193, 7)   # Golden yellow
THUMBNAIL_BG_GRADIENT = [(26, 26, 46), (22, 33, 62)]  # Dark blue gradient

# ─── Channel Branding ────────────────────────────────────────────────────────
CHANNEL_NAME = "BookGyaan"
CHANNEL_TAGLINE = "किताबों की दुनिया"
CHANNEL_HANDLE = "@bookgyaan24-c1n"

# ─── YouTube Upload Settings ─────────────────────────────────────────────────
YOUTUBE_CLIENT_SECRETS_FILE = os.getenv("YOUTUBE_CLIENT_SECRETS", str(BASE_DIR / "client_secrets.json"))
YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
YOUTUBE_CATEGORY_ID = "22"  # "People & Blogs" — good for book summaries
YOUTUBE_DEFAULT_LANGUAGE = "hi"
YOUTUBE_PRIVACY_STATUS = "unlisted"  # "public", "private", or "unlisted"

# ─── Script Generation Prompt ────────────────────────────────────────────────
SCRIPT_SYSTEM_PROMPT = """You are a professional Hindi content writer for the YouTube channel "BookGyaan" (बुकज्ञान).
Your job is to create engaging, insightful book summary scripts in Hindi that:
1. Hook viewers in the first 10 seconds
2. Break down key concepts clearly
3. Use relatable real-life examples
4. End with actionable takeaways
5. Sound natural and conversational (not robotic)

Output format: Return ONLY valid JSON with the exact structure specified. No markdown, no code blocks, just raw JSON."""

SCRIPT_USER_PROMPT_TEMPLATE = """Create a detailed Hindi book summary video script for:

📖 Book: "{book_name}"
✍️ Author: "{author}"

Requirements:
- Total narration should be 8-12 minutes when spoken
- Create exactly {num_scenes} scenes
- First scene: Hook + book introduction (30-45 seconds)
- Last scene: Key takeaways + call to action (45-60 seconds)
- Middle scenes: Core concepts and lessons from the book
- Use simple, conversational Hindi (mix Hinglish where natural)
- Include powerful quotes from the book (translated to Hindi)

Return ONLY this JSON structure:
{{
    "title": "Book Name - बुक समरी in Hindi | BookGyaan",
    "description": "A YouTube-optimized description in Hindi with relevant keywords, chapters/timestamps, and call to action (subscribe, like, comment). 200-300 words.",
    "tags": ["list", "of", "15-20", "relevant", "tags", "in", "hindi", "and", "english"],
    "scenes": [
        {{
            "scene_number": 1,
            "narration_hindi": "Full Hindi narration text for this scene. Should be 50-100 words.",
            "visual_prompt": "English prompt for AI image generation — describe the concept visually. Be specific about style: warm colors, minimalist illustration, conceptual art.",
            "scene_title": "Short Hindi title for this scene"
        }}
    ]
}}"""
