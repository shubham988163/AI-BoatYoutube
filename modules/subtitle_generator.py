"""
BookGyaan - Subtitle Generator
================================
Creates SRT subtitle files from the video script with proper timing.
"""

import sys
from pathlib import Path
from pydub import AudioSegment

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import TEMP_DIR


def generate_subtitles(scenes: list, audio_paths: list, output_path: str = None) -> str:
    """
    Generate an SRT subtitle file from scenes and their audio durations.
    
    Args:
        scenes: List of scene dicts with 'narration_hindi'
        audio_paths: List of audio file paths matching scenes
        output_path: Path to save the .srt file
    
    Returns:
        Path to the generated .srt file
    """
    output_path = output_path or str(TEMP_DIR / "subtitles.srt")

    print(f"\n[SUB] Generating subtitles...")

    srt_entries = []
    current_time_ms = 0
    entry_num = 1

    for i, (scene, audio_path) in enumerate(zip(scenes, audio_paths)):
        narration = scene["narration_hindi"]

        # Get audio duration
        if audio_path and Path(audio_path).exists():
            audio = AudioSegment.from_mp3(audio_path)
            duration_ms = len(audio)
        else:
            # Estimate: ~6 words per second for Hindi
            word_count = len(narration.split())
            duration_ms = int((word_count / 6) * 1000)

        # Split narration into subtitle chunks (~10-12 words each)
        chunks = _split_into_chunks(narration, max_words=10)
        chunk_duration_ms = duration_ms // max(len(chunks), 1)

        for chunk in chunks:
            start_ms = current_time_ms
            end_ms = current_time_ms + chunk_duration_ms

            srt_entries.append({
                "number": entry_num,
                "start": _ms_to_srt_time(start_ms),
                "end": _ms_to_srt_time(end_ms),
                "text": chunk
            })

            current_time_ms = end_ms
            entry_num += 1

    # Write SRT file
    with open(output_path, "w", encoding="utf-8") as f:
        for entry in srt_entries:
            f.write(f"{entry['number']}\n")
            f.write(f"{entry['start']} --> {entry['end']}\n")
            f.write(f"{entry['text']}\n\n")

    print(f"   [OK] Generated {len(srt_entries)} subtitle entries")
    print(f"   [OK] Saved to: {output_path}")
    return output_path


def _split_into_chunks(text: str, max_words: int = 10) -> list:
    """Split text into subtitle-sized chunks."""
    words = text.split()
    chunks = []
    current_chunk = []

    for word in words:
        current_chunk.append(word)

        # Split at punctuation or max words
        if (len(current_chunk) >= max_words or
            word.endswith(('।', '|', '.', '!', '?', ',', ':', ';'))):
            chunks.append(" ".join(current_chunk))
            current_chunk = []

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def _ms_to_srt_time(ms: int) -> str:
    """Convert milliseconds to SRT timestamp format (HH:MM:SS,mmm)."""
    hours = ms // 3600000
    ms %= 3600000
    minutes = ms // 60000
    ms %= 60000
    seconds = ms // 1000
    milliseconds = ms % 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def parse_srt(srt_path: str) -> list:
    """Parse an SRT file into a list of subtitle entries."""
    entries = []
    with open(srt_path, "r", encoding="utf-8") as f:
        content = f.read().strip()
    
    blocks = content.split("\n\n")
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) >= 3:
            time_parts = lines[1].split(" --> ")
            entries.append({
                "number": int(lines[0]),
                "start": time_parts[0].strip(),
                "end": time_parts[1].strip(),
                "text": "\n".join(lines[2:])
            })
    return entries


# ─── CLI Usage ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Demo
    demo_scenes = [
        {"narration_hindi": "नमस्कार दोस्तों, बुकज्ञान में आपका स्वागत है। आज हम एक शानदार किताब के बारे में बात करेंगे।", "scene_number": 1},
        {"narration_hindi": "यह किताब हमें सिखाती है कि छोटी-छोटी आदतें कैसे बड़े बदलाव ला सकती हैं।", "scene_number": 2},
    ]
    demo_audio = [None, None]

    srt_path = generate_subtitles(demo_scenes, demo_audio)
    print(f"\n SRT Content:")
    with open(srt_path, "r", encoding="utf-8") as f:
        print(f.read())
