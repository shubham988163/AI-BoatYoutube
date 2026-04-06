"""
BookGyaan - AI Image Generator
================================
Generates visuals for video scenes using DALL-E 3 or free Pexels stock images.
"""

import os
import sys
import time
import requests
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import (
    IMAGE_PROVIDER, OPENAI_API_KEY, PEXELS_API_KEY,
    IMAGE_WIDTH, IMAGE_HEIGHT, DALLE_MODEL, DALLE_QUALITY,
    TEMP_DIR
)


def generate_scene_images(scenes: list, output_dir: Path = None) -> list:
    """
    Generate images for all scenes.
    
    Args:
        scenes: List of scene dicts with 'visual_prompt' field
        output_dir: Directory to save images (default: temp/images)
    
    Returns:
        List of image file paths in scene order
    """
    output_dir = output_dir or TEMP_DIR / "images"
    output_dir.mkdir(parents=True, exist_ok=True)

    image_paths = []
    total = len(scenes)
    provider = IMAGE_PROVIDER

    print(f"\n[IMG] Generating images for {total} scenes...")
    print(f"   Provider: {provider} | Resolution: {IMAGE_WIDTH}x{IMAGE_HEIGHT}")

    for i, scene in enumerate(scenes):
        scene_num = scene.get("scene_number", i + 1)
        prompt = scene["visual_prompt"]
        output_path = output_dir / f"scene_{scene_num:02d}.png"

        print(f"   [ART] Scene {scene_num}/{total}: {prompt[:50]}...")

        try:
            if provider == "dalle":
                _generate_with_dalle(prompt, str(output_path))
            elif provider == "pexels":
                _download_from_pexels(prompt, str(output_path))
            else:
                _generate_placeholder(prompt, str(output_path), scene_num)

            image_paths.append(str(output_path))
            print(f"       [OK] Saved: {output_path.name}")
        except Exception as e:
            print(f"       [ERROR] {e}")
            # Generate a text-based placeholder
            _generate_placeholder(prompt, str(output_path), scene_num)
            image_paths.append(str(output_path))
            print(f"       [FALLBACK] Using placeholder instead")

        # Rate limiting
        if provider == "dalle":
            time.sleep(1)

    successful = sum(1 for p in image_paths if p is not None)
    print(f"\n   [OK] Generated {successful}/{total} images")
    return image_paths


def _generate_with_dalle(prompt: str, output_path: str):
    """Generate image using OpenAI DALL-E 3."""
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not set for DALL-E image generation.")

    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)

    # Enhance prompt for book summary visuals
    enhanced_prompt = (
        f"Create a cinematic, high-quality illustration for a YouTube book summary video. "
        f"Style: Modern digital art, warm color palette, soft lighting, "
        f"minimalist conceptual illustration. NO text in image. "
        f"Scene: {prompt}"
    )

    response = client.images.generate(
        model=DALLE_MODEL,
        prompt=enhanced_prompt,
        n=1,
        size="1792x1024",  # Closest to 16:9 for DALL-E 3
        quality=DALLE_QUALITY
    )

    image_url = response.data[0].url
    _download_image(image_url, output_path)


def _download_from_pexels(query: str, output_path: str):
    """Download a relevant stock image from Pexels (free)."""
    if not PEXELS_API_KEY:
        raise ValueError("PEXELS_API_KEY not set. Get a free key at https://www.pexels.com/api/")

    headers = {"Authorization": PEXELS_API_KEY}
    # Simplify the prompt to key search terms
    search_query = " ".join(query.split()[:5])

    url = "https://api.pexels.com/v1/search"
    params = {
        "query": search_query,
        "per_page": 3,
        "orientation": "landscape",
        "size": "large"
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()

    if not data.get("photos"):
        raise ValueError(f"No images found on Pexels for: {search_query}")

    # Use the first image's landscape version
    photo = data["photos"][0]
    image_url = photo["src"]["landscape"]
    _download_image(image_url, output_path)


def _download_image(url: str, output_path: str):
    """Download an image from a URL."""
    response = requests.get(url, timeout=60)
    response.raise_for_status()

    with open(output_path, "wb") as f:
        f.write(response.content)


def _generate_placeholder(prompt: str, output_path: str, scene_num: int):
    """Generate a text-based placeholder image using Pillow."""
    from PIL import Image, ImageDraw, ImageFont

    # Create a gradient background
    img = Image.new("RGB", (IMAGE_WIDTH, IMAGE_HEIGHT))
    draw = ImageDraw.Draw(img)

    # Dark gradient effect
    for y in range(IMAGE_HEIGHT):
        ratio = y / IMAGE_HEIGHT
        r = int(20 + ratio * 15)
        g = int(20 + ratio * 25)
        b = int(40 + ratio * 35)
        draw.line([(0, y), (IMAGE_WIDTH, y)], fill=(r, g, b))

    # Add scene number circle
    cx, cy = IMAGE_WIDTH // 2, IMAGE_HEIGHT // 2 - 40
    radius = 60
    draw.ellipse(
        [cx - radius, cy - radius, cx + radius, cy + radius],
        fill=(255, 193, 7),
        outline=(255, 220, 100),
        width=3
    )

    # Scene number text
    try:
        font_large = ImageFont.truetype("arial.ttf", 48)
        font_small = ImageFont.truetype("arial.ttf", 24)
    except OSError:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    scene_text = str(scene_num)
    bbox = draw.textbbox((0, 0), scene_text, font=font_large)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((cx - tw // 2, cy - th // 2), scene_text, fill=(0, 0, 0), font=font_large)

    # Prompt text (truncated)
    prompt_short = prompt[:80] + "..." if len(prompt) > 80 else prompt
    bbox2 = draw.textbbox((0, 0), prompt_short, font=font_small)
    tw2 = bbox2[2] - bbox2[0]
    draw.text(
        (cx - tw2 // 2, cy + radius + 30),
        prompt_short,
        fill=(200, 200, 200),
        font=font_small
    )

    # BookGyaan watermark
    watermark = "BookGyaan"
    draw.text((30, IMAGE_HEIGHT - 50), watermark, fill=(100, 100, 100), font=font_small)

    img.save(output_path, "PNG")


# ─── CLI Usage ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate scene images")
    parser.add_argument("--prompt", help="Visual prompt for image generation")
    parser.add_argument("--output", default="test_image.png", help="Output file")
    parser.add_argument("--provider", choices=["dalle", "pexels", "placeholder"], default="placeholder")
    args = parser.parse_args()

    if args.prompt:
        if args.provider == "placeholder":
            _generate_placeholder(args.prompt, args.output, 1)
        elif args.provider == "dalle":
            _generate_with_dalle(args.prompt, args.output)
        elif args.provider == "pexels":
            _download_from_pexels(args.prompt, args.output)
        print(f"[OK] Image saved to: {args.output}")
    else:
        print("Provide --prompt to generate an image")
