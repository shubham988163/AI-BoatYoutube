"""
================================================================
           BookGyaan AI Video Generator
   Automated Hindi Book Summary YouTube Video Creation

   Channel: @bookgyaan24-c1n
   Usage:
     python main.py --book "Atomic Habits" --author "James Clear"
================================================================
"""

import argparse
import json
import sys
import time
import re
import os
from pathlib import Path

# Fix Windows console encoding for Hindi/emoji characters
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    os.environ["PYTHONIOENCODING"] = "utf-8"

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config.settings import OUTPUT_DIR, TEMP_DIR
from modules.script_generator import generate_script
from modules.tts_engine import generate_scene_audio
from modules.image_generator import generate_scene_images
from modules.video_composer import compose_video
from modules.subtitle_generator import generate_subtitles
from modules.thumbnail_generator import generate_thumbnail


def main():
    parser = argparse.ArgumentParser(
        description="BookGyaan AI Video Generator - Create Hindi book summary videos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --book "Atomic Habits" --author "James Clear"
  python main.py --book "Rich Dad Poor Dad" --author "Robert Kiyosaki" --upload
  python main.py --book "Ikigai" --author "Hector Garcia" --scenes 12 --dry-run
  python main.py --book "The Psychology of Money" --author "Morgan Housel" --voice male
        """
    )

    parser.add_argument("--book", required=True, help="Book name")
    parser.add_argument("--author", required=True, help="Author name")
    parser.add_argument("--scenes", type=int, default=15, help="Number of scenes (default: 15)")
    parser.add_argument("--voice", choices=["male", "female"], default="female",
                        help="Narrator voice (default: female)")
    parser.add_argument("--upload", action="store_true", help="Upload to YouTube after rendering")
    parser.add_argument("--privacy", choices=["public", "private", "unlisted"],
                        default="unlisted", help="YouTube privacy (default: unlisted)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Only generate script, don't render video")
    parser.add_argument("--skip-images", action="store_true",
                        help="Skip AI image generation (use placeholders)")
    parser.add_argument("--review", action="store_true",
                        help="Pause after script generation for review")
    parser.add_argument("--music", help="Path to background music file")
    parser.add_argument("--resume-from", choices=["script", "audio", "images", "video"],
                        help="Resume from a specific step (uses cached data)")

    args = parser.parse_args()

    # Set voice based on argument
    if args.voice == "male":
        import config.settings as settings
        settings.TTS_VOICE = "hi-IN-MadhurNeural"

    # Skip images -> use placeholder provider
    if args.skip_images:
        import config.settings as settings
        settings.IMAGE_PROVIDER = "placeholder"

    # Create safe filename from book name
    safe_name = _sanitize_filename(args.book)
    project_dir = TEMP_DIR / safe_name
    project_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 65)
    print("  BookGyaan AI Video Generator")
    print("=" * 65)
    print(f"  Book:   {args.book}")
    print(f"  Author: {args.author}")
    print(f"  Scenes: {args.scenes}")
    print(f"  Voice:  {args.voice}")
    print(f"  Upload: {'Yes' if args.upload else 'No'}")
    print("=" * 65)

    start_time = time.time()

    try:
        # --- Step 1: Generate Script ---
        step = args.resume_from or "script"

        if step == "script":
            print("\n" + "-" * 50)
            print("[STEP 1/6] Generating Script")
            print("-" * 50)

            script = generate_script(args.book, args.author, args.scenes)

            # Save script for resume
            script_path = project_dir / "script.json"
            with open(script_path, "w", encoding="utf-8") as f:
                json.dump(script, f, ensure_ascii=False, indent=2)

            print(f"\n Script Preview:")
            print(f"   Title: {script['title']}")
            print(f"   Scenes: {len(script['scenes'])}")
            for s in script['scenes'][:3]:
                print(f"   Scene {s['scene_number']}: {s['narration_hindi'][:60]}...")
            if len(script['scenes']) > 3:
                print(f"   ... and {len(script['scenes']) - 3} more scenes")

            if args.dry_run:
                print(f"\n[DONE] Dry run complete! Script saved to: {script_path}")
                return

            if args.review:
                print(f"\n[PAUSE] Script saved to: {script_path}")
                print("   Review it and press Enter to continue (or Ctrl+C to abort)...")
                input()
                with open(script_path, "r", encoding="utf-8") as f:
                    script = json.load(f)

            step = "audio"
        else:
            script_path = project_dir / "script.json"
            with open(script_path, "r", encoding="utf-8") as f:
                script = json.load(f)
            print(f"   [CACHE] Loaded cached script: {script_path}")

        scenes = script["scenes"]

        # --- Step 2: Generate Audio ---
        if step == "audio":
            print("\n" + "-" * 50)
            print("[STEP 2/6] Generating Hindi Speech")
            print("-" * 50)

            audio_dir = project_dir / "audio"
            audio_paths = generate_scene_audio(scenes, audio_dir)

            _save_paths(project_dir / "audio_paths.json", audio_paths)
            step = "images"
        else:
            audio_paths = _load_paths(project_dir / "audio_paths.json")
            print(f"   [CACHE] Loaded cached audio: {len(audio_paths)} files")

        # --- Step 3: Generate Images ---
        if step == "images":
            print("\n" + "-" * 50)
            print("[STEP 3/6] Generating Visuals")
            print("-" * 50)

            image_dir = project_dir / "images"
            image_paths = generate_scene_images(scenes, image_dir)

            _save_paths(project_dir / "image_paths.json", image_paths)
            step = "video"
        else:
            image_paths = _load_paths(project_dir / "image_paths.json")
            print(f"   [CACHE] Loaded cached images: {len(image_paths)} files")

        # --- Step 4: Generate Subtitles ---
        print("\n" + "-" * 50)
        print("[STEP 4/6] Generating Subtitles")
        print("-" * 50)

        subtitle_path = str(project_dir / "subtitles.srt")
        generate_subtitles(scenes, audio_paths, subtitle_path)

        # --- Step 5: Compose Video ---
        print("\n" + "-" * 50)
        print("[STEP 5/6] Composing Final Video")
        print("-" * 50)

        output_filename = f"{safe_name}.mp4"
        video_path = compose_video(
            scenes=scenes,
            audio_paths=audio_paths,
            image_paths=image_paths,
            output_filename=output_filename,
            subtitle_path=subtitle_path,
            background_music_path=args.music
        )

        # --- Step 6: Generate Thumbnail ---
        print("\n" + "-" * 50)
        print("[STEP 6/6] Generating Thumbnail")
        print("-" * 50)

        first_image = image_paths[0] if image_paths else None
        thumbnail_path = generate_thumbnail(
            book_name=args.book,
            author=args.author,
            scene_image_path=first_image
        )

        # --- Upload to YouTube ---
        if args.upload:
            print("\n" + "-" * 50)
            print("[BONUS] Uploading to YouTube")
            print("-" * 50)

            from modules.youtube_uploader import upload_video

            result = upload_video(
                video_path=video_path,
                title=script["title"],
                description=script["description"],
                tags=script["tags"],
                thumbnail_path=thumbnail_path,
                privacy_status=args.privacy
            )

            print(f"\n[DONE] Video live at: {result['url']}")

        # --- Summary ---
        elapsed = time.time() - start_time
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)

        print("\n" + "=" * 65)
        print("  VIDEO GENERATION COMPLETE!")
        print("=" * 65)
        print(f"  Video:     {video_path}")
        print(f"  Thumbnail: {thumbnail_path}")
        print(f"  Subtitles: {subtitle_path}")
        print(f"  Script:    {project_dir / 'script.json'}")
        print(f"  Time:      {minutes}m {seconds}s")
        print("=" * 65)

        if not args.upload:
            print(f"\n  To upload: python main.py --book \"{args.book}\" --author \"{args.author}\" --resume-from video --upload")

    except KeyboardInterrupt:
        print("\n\n[WARN] Interrupted! You can resume with --resume-from <step>")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def _sanitize_filename(name: str) -> str:
    """Convert a book name to a safe filename."""
    name = name.lower().strip()
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'[\s]+', '_', name)
    return name[:50]


def _save_paths(path: Path, paths: list):
    """Save a list of file paths to JSON."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(paths, f, ensure_ascii=False, indent=2)


def _load_paths(path: Path) -> list:
    """Load a list of file paths from JSON."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    main()
