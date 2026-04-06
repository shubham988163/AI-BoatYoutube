"""
BookGyaan - Thumbnail Generator
=================================
Creates eye-catching YouTube thumbnails with book-themed design.
"""

import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import (
    THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT, THUMBNAIL_FONT_SIZE,
    THUMBNAIL_ACCENT_COLOR, THUMBNAIL_BG_GRADIENT,
    CHANNEL_NAME, OUTPUT_DIR, TEMP_DIR
)


def generate_thumbnail(
    book_name: str,
    author: str,
    scene_image_path: str = None,
    output_path: str = None
) -> str:
    """
    Generate a YouTube thumbnail for the book summary video.
    
    Args:
        book_name: Name of the book
        author: Author name
        scene_image_path: Optional path to a scene image to use as background
        output_path: Path to save the thumbnail
    
    Returns:
        Path to the generated thumbnail
    """
    from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

    output_path = output_path or str(OUTPUT_DIR / f"thumbnail_{_sanitize(book_name)}.jpg")

    print(f"\n[THUMB] Generating thumbnail for: {book_name}")

    # Create base image
    img = Image.new("RGB", (THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT))
    draw = ImageDraw.Draw(img)

    # Use scene image as background if available
    if scene_image_path and Path(scene_image_path).exists():
        try:
            bg = Image.open(scene_image_path)
            bg = bg.resize((THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), Image.LANCZOS)
            # Darken and blur for readability
            bg = bg.filter(ImageFilter.GaussianBlur(radius=4))
            enhancer = ImageEnhance.Brightness(bg)
            bg = enhancer.enhance(0.4)
            img.paste(bg)
            draw = ImageDraw.Draw(img)
        except Exception:
            _draw_gradient_bg(draw)
    else:
        _draw_gradient_bg(draw)

    # Add accent stripe on left
    accent_color = THUMBNAIL_ACCENT_COLOR
    draw.rectangle(
        [0, 0, 18, THUMBNAIL_HEIGHT],
        fill=accent_color
    )

    # Add decorative elements
    _draw_decorative_elements(draw, accent_color)

    # Load fonts
    font_title = _load_font(THUMBNAIL_FONT_SIZE)
    font_author = _load_font(int(THUMBNAIL_FONT_SIZE * 0.45))
    font_brand = _load_font(int(THUMBNAIL_FONT_SIZE * 0.38))
    font_badge = _load_font(int(THUMBNAIL_FONT_SIZE * 0.32))

    # ─── Layout ──────────────────────────────────────────────────────────

    # "Book Summary" badge at top
    badge_text = "BOOK SUMMARY"
    badge_y = 50
    badge_padding = 15
    bbox_badge = draw.textbbox((0, 0), badge_text, font=font_badge)
    badge_w = bbox_badge[2] - bbox_badge[0] + badge_padding * 2
    badge_h = bbox_badge[3] - bbox_badge[1] + badge_padding * 2

    draw.rounded_rectangle(
        [60, badge_y, 60 + badge_w, badge_y + badge_h],
        radius=8,
        fill=accent_color
    )
    draw.text(
        (60 + badge_padding, badge_y + badge_padding - 2),
        badge_text,
        fill=(0, 0, 0),
        font=font_badge
    )

    # Book title (main text — large, bold)
    title_y = badge_y + badge_h + 40
    title_max_width = THUMBNAIL_WIDTH - 140  # padding on both sides

    # Wrap title text
    title_lines = _wrap_text(draw, book_name.upper(), font_title, title_max_width)
    for line in title_lines:
        # Text shadow
        draw.text((62, title_y + 3), line, fill=(0, 0, 0), font=font_title)
        # Main text
        draw.text((60, title_y), line, fill="white", font=font_title)
        bbox_line = draw.textbbox((0, 0), line, font=font_title)
        title_y += (bbox_line[3] - bbox_line[1]) + 10

    # Author name
    author_y = title_y + 20
    author_text = f"— {author}"
    draw.text((62, author_y + 2), author_text, fill=(0, 0, 0), font=font_author)
    draw.text((60, author_y), author_text, fill=accent_color, font=font_author)

    # Channel branding at bottom
    brand_y = THUMBNAIL_HEIGHT - 80
    draw.rectangle(
        [0, brand_y - 10, THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT],
        fill=(0, 0, 0, 128)
    )
    brand_text = f"{CHANNEL_NAME}"
    draw.text((60, brand_y + 5), brand_text, fill=accent_color, font=font_brand)

    # "Hindi" language badge at top-right
    hindi_badge = "हिंदी"
    hindi_bbox = draw.textbbox((0, 0), hindi_badge, font=font_badge)
    hindi_w = hindi_bbox[2] - hindi_bbox[0] + 20
    hindi_h = hindi_bbox[3] - hindi_bbox[1] + 16
    hindi_x = THUMBNAIL_WIDTH - hindi_w - 40
    hindi_y = 50

    draw.rounded_rectangle(
        [hindi_x, hindi_y, hindi_x + hindi_w, hindi_y + hindi_h],
        radius=8,
        fill=(220, 50, 50)
    )
    draw.text(
        (hindi_x + 10, hindi_y + 6),
        hindi_badge,
        fill="white",
        font=font_badge
    )

    # Save
    img.save(output_path, "JPEG", quality=95)
    print(f"   [OK] Thumbnail saved: {output_path}")

    return output_path


def _draw_gradient_bg(draw):
    """Draw a dark gradient background."""
    color_start = THUMBNAIL_BG_GRADIENT[0]
    color_end = THUMBNAIL_BG_GRADIENT[1]

    for y in range(THUMBNAIL_HEIGHT):
        ratio = y / THUMBNAIL_HEIGHT
        r = int(color_start[0] + (color_end[0] - color_start[0]) * ratio)
        g = int(color_start[1] + (color_end[1] - color_start[1]) * ratio)
        b = int(color_start[2] + (color_end[2] - color_start[2]) * ratio)
        draw.line([(0, y), (THUMBNAIL_WIDTH, y)], fill=(r, g, b))


def _draw_decorative_elements(draw, accent_color):
    """Add subtle decorative geometric elements."""
    # Diagonal accent lines
    for offset in range(0, 300, 40):
        draw.line(
            [(THUMBNAIL_WIDTH - 200 + offset, 0),
             (THUMBNAIL_WIDTH + offset, THUMBNAIL_HEIGHT)],
            fill=(*accent_color, 30),
            width=2
        )

    # Corner accent
    corner_size = 120
    draw.polygon(
        [(THUMBNAIL_WIDTH, 0),
         (THUMBNAIL_WIDTH - corner_size, 0),
         (THUMBNAIL_WIDTH, corner_size)],
        fill=(*accent_color, 60)
    )


def _load_font(size: int):
    """Load a font, falling back to default if needed."""
    from PIL import ImageFont

    font_paths = [
        "arial.ttf",
        "arialbd.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf",
    ]

    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue

    return ImageFont.load_default()


def _wrap_text(draw, text: str, font, max_width: int) -> list:
    """Wrap text to fit within max_width."""
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]

    if current_line:
        lines.append(" ".join(current_line))

    return lines[:3]  # Max 3 lines


def _sanitize(name: str) -> str:
    """Sanitize filename."""
    import re
    name = name.lower().strip()
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'[\s]+', '_', name)
    return name[:30]


# ─── CLI Usage ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate YouTube thumbnail")
    parser.add_argument("--book", required=True, help="Book name")
    parser.add_argument("--author", required=True, help="Author name")
    parser.add_argument("--bg-image", help="Background image path")
    parser.add_argument("--output", help="Output path")
    args = parser.parse_args()

    generate_thumbnail(
        args.book,
        args.author,
        scene_image_path=args.bg_image,
        output_path=args.output
    )
