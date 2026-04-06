"""
BookGyaan - Hindi Text-to-Speech Engine
=========================================
Uses Microsoft Edge-TTS for free, high-quality Hindi speech synthesis.
"""

import asyncio
import sys
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import TTS_VOICE, TTS_RATE, TTS_PITCH, TEMP_DIR


async def _generate_speech_async(text: str, output_path: str, voice: str = None, rate: str = None) -> str:
    """Async implementation of speech generation using edge-tts."""
    import edge_tts

    voice = voice or TTS_VOICE
    rate = rate or TTS_RATE

    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=rate,
        pitch=TTS_PITCH
    )

    await communicate.save(output_path)
    return output_path


def generate_speech(text: str, output_path: str, voice: str = None, rate: str = None) -> str:
    """
    Generate Hindi speech from text.

    Args:
        text: Hindi text to convert to speech
        output_path: Path to save the audio file (.mp3)
        voice: TTS voice name (default from settings)
        rate: Speech rate (e.g., "+0%", "-10%", "+10%")

    Returns:
        Path to the generated audio file
    """
    try:
        loop = asyncio.get_running_loop()
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            result = pool.submit(
                asyncio.run,
                _generate_speech_async(text, output_path, voice, rate)
            ).result()
        return result
    except RuntimeError:
        return asyncio.run(_generate_speech_async(text, output_path, voice, rate))


def generate_scene_audio(scenes: list, output_dir: Path = None) -> list:
    """
    Generate audio files for all scenes.

    Args:
        scenes: List of scene dicts with 'narration_hindi' field
        output_dir: Directory to save audio files (default: temp/)

    Returns:
        List of audio file paths in scene order
    """
    output_dir = output_dir or TEMP_DIR / "audio"
    output_dir.mkdir(parents=True, exist_ok=True)

    audio_paths = []
    total = len(scenes)

    print(f"\n[TTS] Generating Hindi speech for {total} scenes...")
    print(f"   Voice: {TTS_VOICE} | Rate: {TTS_RATE}")

    for i, scene in enumerate(scenes):
        scene_num = scene.get("scene_number", i + 1)
        text = scene["narration_hindi"]
        output_path = str(output_dir / f"scene_{scene_num:02d}.mp3")

        print(f"   [MIC] Scene {scene_num}/{total}: {text[:40]}...")

        try:
            generate_speech(text, output_path)
            audio_paths.append(output_path)
            print(f"       [OK] Saved: {output_path}")
        except Exception as e:
            print(f"       [ERROR] {e}")
            audio_paths.append(None)

    successful = sum(1 for p in audio_paths if p is not None)
    print(f"\n   [OK] Generated {successful}/{total} audio files")
    return audio_paths


async def list_hindi_voices():
    """List all available Hindi voices in Edge-TTS."""
    import edge_tts
    voices = await edge_tts.list_voices()
    hindi_voices = [v for v in voices if v["Locale"].startswith("hi-")]

    print("\n[VOICES] Available Hindi Voices:")
    print("-" * 60)
    for v in hindi_voices:
        print(f"   {v['ShortName']:30s} | {v['Gender']:8s} | {v['Locale']}")
    return hindi_voices


# --- CLI Usage ----------------------------------------------------------------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Hindi Text-to-Speech")
    parser.add_argument("--text", help="Hindi text to convert")
    parser.add_argument("--output", default="test_speech.mp3", help="Output file")
    parser.add_argument("--list-voices", action="store_true", help="List Hindi voices")
    args = parser.parse_args()

    if args.list_voices:
        asyncio.run(list_hindi_voices())
    elif args.text:
        generate_speech(args.text, args.output)
        print(f"[OK] Audio saved to: {args.output}")
    else:
        demo_text = "Namaskaar doston, BookGyaan mein aapka swaagat hai. Aaj hum ek shaandaar kitaab ke baare mein baat karenge."
        output = str(TEMP_DIR / "demo_hindi.mp3")
        generate_speech(demo_text, output)
        print(f"[OK] Demo audio saved to: {output}")
