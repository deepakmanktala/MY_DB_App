#!/usr/bin/env python3
"""
faang_video_creator.py
Generates a slide-based MP4 from faang_database_youtube_package/shot_list.json.

Each scene becomes a timed slide with:
  - Scene number + title
  - On-screen text (large)
  - Voiceover text (bottom panel)

Requirements:
    pip install moviepy Pillow numpy

FFmpeg must be installed and on PATH (MoviePy needs it).
Download: https://ffmpeg.org/download.html  (add bin/ folder to PATH)

Output:
    faang_database_video.mp4  (in current directory)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageClip, concatenate_videoclips

# ── Config ─────────────────────────────────────────────────────────────────────
SHOT_LIST   = Path("faang_database_youtube_package/shot_list.json")
OUTPUT_FILE = Path("faang_database_video.mp4")
WIDTH, HEIGHT = 1920, 1080
FPS = 24

# Colour palette
BG_COLOR        = (10,  15,  30)    # dark navy
ACCENT_COLOR    = (0,  120, 255)    # bright blue
TITLE_COLOR     = (255, 255, 255)   # white
TEXT_COLOR      = (200, 220, 255)   # light blue-white
SCENE_NUM_COLOR = (0,  200, 150)    # teal
VO_BG_COLOR     = (20,  35,  65)    # slightly lighter navy
VO_TEXT_COLOR   = (160, 180, 210)   # muted blue-white


# ── Font helpers ───────────────────────────────────────────────────────────────
def _try_fonts(candidates: list[str], size: int) -> ImageFont.FreeTypeFont:
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    if bold:
        paths = [
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/Arial Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ]
    else:
        paths = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/Arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]
    return _try_fonts(paths, size)


# ── Text wrapping ──────────────────────────────────────────────────────────────
def wrap_text(
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
    draw: ImageDraw.ImageDraw,
) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = (current + " " + word).strip()
        w = draw.textbbox((0, 0), candidate, font=font)[2]
        if w <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


# ── Slide renderer ─────────────────────────────────────────────────────────────
def make_slide(scene: dict) -> Image.Image:
    img  = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Top accent bar
    draw.rectangle([(0, 0), (WIDTH, 8)], fill=ACCENT_COLOR)

    # Fonts
    f_scene_num = get_font(30)
    f_title     = get_font(68, bold=True)
    f_body      = get_font(52)
    f_vo_label  = get_font(26)
    f_vo        = get_font(30)

    # --- Scene number (top-left) ---
    draw.text((60, 26), f"SCENE {scene['scene']:02d}", font=f_scene_num, fill=SCENE_NUM_COLOR)

    # --- Duration badge (top-right) ---
    dur_text = f"{scene['duration_sec']} sec"
    dur_w    = draw.textbbox((0, 0), dur_text, font=f_scene_num)[2]
    draw.text((WIDTH - dur_w - 60, 26), dur_text, font=f_scene_num, fill=ACCENT_COLOR)

    # --- Title ---
    title_y = 100
    draw.text((60, title_y), scene["title"], font=f_title, fill=TITLE_COLOR)
    title_h = draw.textbbox((60, title_y), scene["title"], font=f_title)[3]

    # Divider under title
    line_y = title_h + 18
    draw.rectangle([(60, line_y), (WIDTH - 60, line_y + 4)], fill=ACCENT_COLOR)

    # --- On-screen text (main body) ---
    body_y    = line_y + 44
    body_lines = wrap_text(scene["on_screen_text"], f_body, WIDTH - 120, draw)
    for line in body_lines:
        draw.text((60, body_y), line, font=f_body, fill=TEXT_COLOR)
        body_y += draw.textbbox((0, 0), line, font=f_body)[3] + 14

    # --- Voiceover panel (bottom 260px) ---
    vo_top = HEIGHT - 272
    draw.rectangle([(0, vo_top), (WIDTH, HEIGHT - 8)], fill=VO_BG_COLOR)
    draw.rectangle([(0, vo_top), (WIDTH, vo_top + 4)], fill=ACCENT_COLOR)

    draw.text((60, vo_top + 14), "VOICEOVER", font=f_vo_label, fill=ACCENT_COLOR)

    vo_y     = vo_top + 50
    vo_lines = wrap_text(scene["voiceover"], f_vo, WIDTH - 120, draw)
    for line in vo_lines[:5]:   # cap at 5 lines so it fits
        draw.text((60, vo_y), line, font=f_vo, fill=VO_TEXT_COLOR)
        vo_y += draw.textbbox((0, 0), line, font=f_vo)[3] + 8

    # Bottom accent bar
    draw.rectangle([(0, HEIGHT - 8), (WIDTH, HEIGHT)], fill=ACCENT_COLOR)

    return img


# ── Main ───────────────────────────────────────────────────────────────────────
def main() -> None:
    if not SHOT_LIST.exists():
        sys.exit(f"ERROR: {SHOT_LIST} not found. Run faang_youtube_package_generator.py first.")

    data   = json.loads(SHOT_LIST.read_text(encoding="utf-8"))
    scenes = data["scenes"]
    total  = data.get("estimated_runtime_sec", sum(s["duration_sec"] for s in scenes))
    mins, secs = divmod(total, 60)

    print(f"Project : {data['project_title']}")
    print(f"Scenes  : {len(scenes)}")
    print(f"Runtime : {mins}:{secs:02d}")
    print(f"Output  : {OUTPUT_FILE.resolve()}\n")

    clips = []
    for scene in scenes:
        print(f"  [{scene['scene']:02d}/{len(scenes)}] {scene['title']:<40} {scene['duration_sec']}s")
        img  = make_slide(scene)
        arr  = np.array(img)
        clip = ImageClip(arr).with_duration(scene["duration_sec"])
        clips.append(clip)

    print("\nConcatenating clips ...")
    final = concatenate_videoclips(clips, method="compose")

    print(f"Writing MP4 (this may take a minute) ...")
    final.write_videofile(
        str(OUTPUT_FILE),
        fps=FPS,
        codec="libx264",
        audio=False,
        logger="bar",
    )
    print(f"\nDone!  {OUTPUT_FILE.resolve()}")
    print("Next step: add your voiceover audio in Canva/CapCut and export the final cut.")


if __name__ == "__main__":
    main()