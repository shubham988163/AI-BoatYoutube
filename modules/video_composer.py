"""
BookGyaan - Video Composer
============================
Assembles the final video from audio, images, subtitles, and music using MoviePy.
"""

import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import (
    VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS, VIDEO_CODEC,
    AUDIO_CODEC, AUDIO_BITRATE,
    CROSSFADE_DURATION, KEN_BURNS_ZOOM, BACKGROUND_MUSIC_VOLUME,
    SUBTITLE_FONT_SIZE, SUBTITLE_FONT_COLOR,
    MUSIC_DIR, OUTPUT_DIR, TEMP_DIR
)


def compose_video(
    scenes: list,
    audio_paths: list,
    image_paths: list,
    output_filename: str,
    subtitle_path: str = None,
    background_music_path: str = None
) -> str:
    """
    Compose the final video from individual components.
    
    Args:
        scenes: List of scene dicts
        audio_paths: List of audio file paths per scene
        image_paths: List of image file paths per scene
        output_filename: Name of the output file (e.g., "atomic_habits.mp4")
        subtitle_path: Path to SRT subtitle file (optional)
        background_music_path: Path to background music file (optional)
    
    Returns:
        Path to the final output video file
    """
    from moviepy import (
        ImageClip, AudioFileClip, concatenate_videoclips,
        CompositeVideoClip, TextClip, CompositeAudioClip,
        ColorClip
    )
    import numpy as np

    output_path = str(OUTPUT_DIR / output_filename)
    print(f"\n[VIDEO] Composing video: {output_filename}")
    print(f"   Resolution: {VIDEO_WIDTH}x{VIDEO_HEIGHT} @ {VIDEO_FPS}fps")

    scene_clips = []

    for i, (scene, audio_path, image_path) in enumerate(zip(scenes, audio_paths, image_paths)):
        scene_num = scene.get("scene_number", i + 1)
        print(f"   [SCENE] Composing scene {scene_num}/{len(scenes)}...")

        # Skip if audio is missing
        if audio_path is None or not Path(audio_path).exists():
            print(f"       [WARN] Skipping scene {scene_num}: no audio")
            continue

        # Load audio
        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration

        # Load and prepare image
        if image_path and Path(image_path).exists():
            img_clip = ImageClip(image_path)
        else:
            # Fallback: dark colored background
            img_clip = ColorClip(
                size=(VIDEO_WIDTH, VIDEO_HEIGHT),
                color=(20, 20, 40)
            )

        # Resize image to fit video dimensions (cover mode)
        img_clip = _resize_cover(img_clip, VIDEO_WIDTH, VIDEO_HEIGHT)

        # Apply Ken Burns effect (subtle zoom)
        img_clip = _apply_ken_burns(img_clip, duration, KEN_BURNS_ZOOM)

        # Set duration and audio
        img_clip = img_clip.with_duration(duration)
        img_clip = img_clip.with_audio(audio_clip)

        # Add subtitle overlay for this scene
        narration = scene.get("narration_hindi", "")
        if narration:
            subtitle_clip = _create_subtitle_overlay(narration, duration, VIDEO_WIDTH, VIDEO_HEIGHT)
            img_clip = CompositeVideoClip([img_clip, subtitle_clip])

        scene_clips.append(img_clip)

    if not scene_clips:
        raise ValueError("No valid scene clips to compose!")

    print(f"\n   [JOIN] Concatenating {len(scene_clips)} scenes...")

    # Concatenate all scenes with crossfade transitions
    if len(scene_clips) > 1 and CROSSFADE_DURATION > 0:
        # Apply crossfade between clips
        final_clips = [scene_clips[0]]
        for clip in scene_clips[1:]:
            final_clips.append(clip.with_effects([]))
        final_video = concatenate_videoclips(final_clips, method="compose")
    else:
        final_video = concatenate_videoclips(scene_clips, method="compose")

    # Add background music if provided
    bg_music_path = background_music_path or _find_background_music()
    if bg_music_path and Path(bg_music_path).exists():
        print(f"   [MUSIC] Adding background music...")
        bg_music = AudioFileClip(bg_music_path)

        # Loop music to match video duration
        if bg_music.duration < final_video.duration:
            loops_needed = int(final_video.duration / bg_music.duration) + 1
            from moviepy import concatenate_audioclips
            bg_music = concatenate_audioclips([bg_music] * loops_needed)

        bg_music = bg_music.subclipped(0, final_video.duration)
        bg_music = bg_music.with_volume_scaled(BACKGROUND_MUSIC_VOLUME)

        # Mix original audio with background music
        final_audio = CompositeAudioClip([final_video.audio, bg_music])
        final_video = final_video.with_audio(final_audio)

    # Calculate total duration
    total_duration = final_video.duration
    minutes = int(total_duration // 60)
    seconds = int(total_duration % 60)
    print(f"   [TIME] Total duration: {minutes}m {seconds}s")

    # Export final video
    print(f"\n   [RENDER] Rendering video (this may take a while)...")
    final_video.write_videofile(
        output_path,
        fps=VIDEO_FPS,
        codec=VIDEO_CODEC,
        audio_codec=AUDIO_CODEC,
        audio_bitrate=AUDIO_BITRATE,
        preset="medium",
        threads=4,
        logger="bar"
    )

    # Clean up
    final_video.close()
    for clip in scene_clips:
        clip.close()

    file_size_mb = Path(output_path).stat().st_size / (1024 * 1024)
    print(f"\n   [OK] Video saved: {output_path}")
    print(f"   [SIZE] File size: {file_size_mb:.1f} MB")

    return output_path


def _resize_cover(clip, target_width: int, target_height: int):
    """Resize clip to cover target dimensions (may crop)."""
    clip_w, clip_h = clip.size
    target_ratio = target_width / target_height
    clip_ratio = clip_w / clip_h

    if clip_ratio > target_ratio:
        # Image is wider — scale by height
        new_height = target_height
        new_width = int(clip_w * (target_height / clip_h))
    else:
        # Image is taller — scale by width
        new_width = target_width
        new_height = int(clip_h * (target_width / clip_w))

    clip = clip.resized((new_width, new_height))

    # Center crop to target
    x_center = new_width // 2
    y_center = new_height // 2
    x1 = x_center - target_width // 2
    y1 = y_center - target_height // 2

    clip = clip.cropped(x1=x1, y1=y1, width=target_width, height=target_height)
    return clip


def _apply_ken_burns(clip, duration: float, zoom_factor: float):
    """Apply a subtle Ken Burns zoom effect to an image clip."""
    import numpy as np

    w, h = clip.size

    def zoom_effect(get_frame, t):
        """Gradually zoom in over the duration."""
        progress = t / duration
        current_zoom = 1.0 + (zoom_factor - 1.0) * progress

        # Calculate crop dimensions
        crop_w = int(w / current_zoom)
        crop_h = int(h / current_zoom)
        x1 = (w - crop_w) // 2
        y1 = (h - crop_h) // 2

        frame = get_frame(t)
        cropped = frame[y1:y1 + crop_h, x1:x1 + crop_w]

        # Resize back to original dimensions
        from PIL import Image
        pil_img = Image.fromarray(cropped)
        pil_img = pil_img.resize((w, h), Image.LANCZOS)
        return np.array(pil_img)

    return clip.transform(zoom_effect)


def _create_subtitle_overlay(text: str, duration: float, video_width: int, video_height: int):
    """Create a subtitle text overlay with background."""
    from moviepy import TextClip, CompositeVideoClip, ColorClip

    # Split into lines if text is long
    words = text.split()
    lines = []
    current_line = []
    for word in words:
        current_line.append(word)
        if len(" ".join(current_line)) > 45:
            lines.append(" ".join(current_line))
            current_line = []
    if current_line:
        lines.append(" ".join(current_line))

    subtitle_text = "\n".join(lines)

    try:
        txt_clip = TextClip(
            text=subtitle_text,
            font_size=SUBTITLE_FONT_SIZE,
            color=SUBTITLE_FONT_COLOR,
            font="Arial",
            text_align="center",
            size=(video_width - 200, None),
            method="caption"
        )
    except Exception:
        # Fallback without specific font
        txt_clip = TextClip(
            text=subtitle_text,
            font_size=36,
            color="white",
            text_align="center",
            size=(video_width - 200, None),
            method="caption"
        )

    # Position at bottom with padding
    txt_clip = txt_clip.with_position(("center", video_height - txt_clip.size[1] - 60))
    txt_clip = txt_clip.with_duration(duration)

    # Create semi-transparent background
    bg_height = txt_clip.size[1] + 30
    bg_clip = ColorClip(
        size=(video_width, bg_height),
        color=(0, 0, 0)
    ).with_opacity(0.6)
    bg_clip = bg_clip.with_position(("center", video_height - bg_height - 45))
    bg_clip = bg_clip.with_duration(duration)

    # Composite subtitle with background
    subtitle_overlay = CompositeVideoClip(
        [bg_clip, txt_clip],
        size=(video_width, video_height)
    ).with_duration(duration)

    return subtitle_overlay


def _find_background_music() -> str:
    """Find a background music file in the assets/music directory."""
    if not MUSIC_DIR.exists():
        return None

    music_files = list(MUSIC_DIR.glob("*.mp3")) + list(MUSIC_DIR.glob("*.wav"))
    if music_files:
        return str(music_files[0])
    return None


# ─── CLI Usage ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Video Composer module — use via main.py")
    print(f"   Output dir: {OUTPUT_DIR}")
    print(f"   Music dir: {MUSIC_DIR}")
    music = _find_background_music()
    print(f"   Background music: {music or 'None found'}")
