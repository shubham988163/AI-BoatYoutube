"""
BookGyaan - Script Generator Module
=====================================
Uses LLM (Gemini or OpenAI) to generate structured Hindi book summary scripts.
"""

import json
import re
import sys
import os
from pathlib import Path

# Fix Windows console encoding for emoji/unicode
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import (
    LLM_PROVIDER, GEMINI_API_KEY, OPENAI_API_KEY,
    GEMINI_MODEL, OPENAI_MODEL,
    SCRIPT_SYSTEM_PROMPT, SCRIPT_USER_PROMPT_TEMPLATE,
    TEMP_DIR
)


def generate_script(book_name: str, author: str, num_scenes: int = 15) -> dict:
    """
    Generate a structured video script for a book summary.

    Args:
        book_name: Name of the book
        author: Author of the book
        num_scenes: Number of scenes to generate (default 15 for ~10 min video)

    Returns:
        dict with keys: title, description, tags, scenes
    """
    print(f"\n[AI] Generating script for: '{book_name}' by {author}")
    print(f"   Provider: {LLM_PROVIDER} | Scenes: {num_scenes}")

    user_prompt = SCRIPT_USER_PROMPT_TEMPLATE.format(
        book_name=book_name,
        author=author,
        num_scenes=num_scenes
    )

    if LLM_PROVIDER == "gemini":
        script = _generate_with_gemini(user_prompt)
    elif LLM_PROVIDER == "openai":
        script = _generate_with_openai(user_prompt)
    else:
        raise ValueError(f"Unknown LLM provider: {LLM_PROVIDER}")

    # Save script to temp for debugging
    script_path = TEMP_DIR / f"{_sanitize_filename(book_name)}_script.json"
    with open(script_path, "w", encoding="utf-8") as f:
        json.dump(script, f, ensure_ascii=False, indent=2)
    print(f"   [OK] Script saved to: {script_path}")
    print(f"   [OK] Generated {len(script.get('scenes', []))} scenes")

    return script


def _generate_with_gemini(user_prompt: str) -> dict:
    """Generate script using Google Gemini API (new google.genai SDK)."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set. Add it to your .env file.")

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=GEMINI_API_KEY)

    print("   [API] Calling Gemini API...")
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=SCRIPT_SYSTEM_PROMPT,
            temperature=0.8,
            top_p=0.95,
            max_output_tokens=8192,
            response_mime_type="application/json"
        )
    )

    return _parse_json_response(response.text)


def _generate_with_openai(user_prompt: str) -> dict:
    """Generate script using OpenAI API."""
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not set. Add it to your .env file.")

    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)

    print("   [API] Calling OpenAI API...")
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SCRIPT_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.8,
        max_tokens=8192,
        response_format={"type": "json_object"}
    )

    return _parse_json_response(response.choices[0].message.content)


def _parse_json_response(text: str) -> dict:
    """Parse JSON from LLM response, handling markdown code blocks."""
    text = text.strip()
    text = re.sub(r'^```(?:json)?\s*', '', text)
    text = re.sub(r'\s*```$', '', text)

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        print(f"   [ERROR] JSON parse error: {e}")
        print(f"   Raw response (first 500 chars): {text[:500]}")
        raise ValueError(f"LLM returned invalid JSON: {e}")

    # Validate required fields
    required = ["title", "description", "tags", "scenes"]
    for field in required:
        if field not in data:
            raise ValueError(f"Missing required field in script: '{field}'")

    if not data["scenes"]:
        raise ValueError("Script has no scenes!")

    # Validate each scene
    for i, scene in enumerate(data["scenes"]):
        for key in ["scene_number", "narration_hindi", "visual_prompt"]:
            if key not in scene:
                raise ValueError(f"Scene {i+1} missing field: '{key}'")

    return data


def _sanitize_filename(name: str) -> str:
    """Convert a book name to a safe filename."""
    name = name.lower().strip()
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'[\s]+', '_', name)
    return name[:50]


# --- CLI Usage ----------------------------------------------------------------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate book summary script")
    parser.add_argument("--book", required=True, help="Book name")
    parser.add_argument("--author", required=True, help="Author name")
    parser.add_argument("--scenes", type=int, default=15, help="Number of scenes")
    args = parser.parse_args()

    script = generate_script(args.book, args.author, args.scenes)
    print(f"\n Title: {script['title']}")
    print(f" Tags: {', '.join(script['tags'][:5])}...")
    for scene in script['scenes']:
        print(f"\n  Scene {scene['scene_number']}: {scene.get('scene_title', 'N/A')}")
        print(f"  {scene['narration_hindi'][:80]}...")
