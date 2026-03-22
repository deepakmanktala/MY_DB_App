#!/usr/bin/env python3
"""
Auto-build a slide deck video locally with MoviePy + FFmpeg placeholders.

What this script does
---------------------
Creates a simple YouTube-style video from:
- slide images (PNG/JPG)
- optional voiceover audio files per scene (MP3/WAV/M4A)
- optional background music
- optional subtitle text burned into each slide

It is designed as a practical starter script, not a full editing suite.

Folder structure expected
-------------------------
project/
  slides/
    scene_01.png
    scene_02.png
    ...
  audio/
    scene_01.mp3
    scene_02.mp3
    ...
  music/
    bgm.mp3                  # optional
  output/
  storyboard.csv            # optional, for text overlays / durations

If a scene audio file exists:
- scene duration = audio duration + padding

If a scene audio file does not exist:
- scene duration = default duration from CLI

Features
--------
- Ken Burns style slow zoom on slides
- Optional text overlay from storyboard.csv
- Optional background music mixed at low volume
- Scene transitions via short crossfade
- Exports final MP4
- Generates a sample project template if requested

Install
-------
pip install moviepy pillow pandas

FFmpeg must be installed and available on PATH.

Examples
--------
1) Create a sample template project:
   python auto_build_slide_video.py --init-template demo_project

2) Build a video from that project:
   python auto_build_slide_video.py --project demo_project --output demo_project/output/final.mp4

3) Build with custom defaults:
   python auto_build_slide_video.py --project demo_project --output demo_project/output/final.mp4 --fps 30 --default-duration 8

Notes
-----
- This script uses moviepy and expects FFmpeg to be installed.
- It does not perform TTS or create images automatically.
- Use Canva/PowerPoint/Figma to make slides, then export to PNG.
"""

from __future__ import annotations

import argparse
import csv
import math
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
from moviepy import (
    AudioFileClip,
    CompositeAudioClip,
    CompositeVideoClip,
    ImageClip,
    TextClip,
    concatenate_videoclips,
)
from moviepy.video.fx import CrossFadeIn
from PIL import Image, ImageDraw, ImageFont


SUPPORTED_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
SUPPORTED_AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".aac", ".ogg"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Auto-build slide deck video locally with MoviePy.")
    parser.add_argument("--project", type=str, help="Project directory containing slides/audio/music.", default=None)
    parser.add_argument("--output", type=str, help="Output MP4 path.", default=None)
    parser.add_argument("--fps", type=int, default=30, help="Frames per second.")
    parser.add_argument("--width", type=int, default=1920, help="Output width.")
    parser.add_argument("--height", type=int, default=1080, help="Output height.")
    parser.add_argument("--default-duration", type=float, default=7.0, help="Fallback scene duration if no audio exists.")
    parser.add_argument("--scene-padding", type=float, default=0.4, help="Extra time added after each scene audio.")
    parser.add_argument("--crossfade", type=float, default=0.35, help="Crossfade duration between scenes.")
    parser.add_argument("--music-volume", type=float, default=0.12, help="Background music volume multiplier.")
    parser.add_argument("--voice-volume", type=float, default=1.0, help="Voiceover volume multiplier.")
    parser.add_argument("--zoom-mode", choices=["in", "out", "alternate", "none"], default="alternate")
    parser.add_argument("--font", type=str, default="Arial", help="Font for overlay text.")
    parser.add_argument("--subtitle-size", type=int, default=42, help="Overlay text font size.")
    parser.add_argument("--bottom-margin", type=int, default=90, help="Bottom margin for text overlay.")
    parser.add_argument("--init-template", type=str, default=None, help="Create a sample project template at this path.")
    return parser.parse_args()


def create_template(project_dir: Path) -> None:
    (project_dir / "slides").mkdir(parents=True, exist_ok=True)
    (project_dir / "audio").mkdir(parents=True, exist_ok=True)
    (project_dir / "music").mkdir(parents=True, exist_ok=True)
    (project_dir / "output").mkdir(parents=True, exist_ok=True)

    # Create simple placeholder slides
    try:
        from PIL import ImageDraw, ImageFont
    except Exception:
        raise RuntimeError("Pillow is required to generate the template slides.")

    for i in range(1, 6):
        img = Image.new("RGB", (1920, 1080), color=(18, 24, 38))
        draw = ImageDraw.Draw(img)
        title = f"Scene {i:02d}"
        subtitle = "Replace this slide with your exported Canva/PowerPoint/PNG slide."
        note = f"Expected file names: scene_{i:02d}.png and optional audio/scene_{i:02d}.mp3"

        draw.text((120, 180), title, fill=(255, 255, 255))
        draw.text((120, 320), subtitle, fill=(200, 210, 220))
        draw.text((120, 420), note, fill=(150, 170, 190))
        img.save(project_dir / "slides" / f"scene_{i:02d}.png")

    storyboard_path = project_dir / "storyboard.csv"
    rows = [
        {"scene": 1, "title": "Hook", "duration_sec": 8, "on_screen_text": "FAANG Database Designs"},
        {"scene": 2, "title": "Problem", "duration_sec": 8, "on_screen_text": "One database cannot do everything"},
        {"scene": 3, "title": "Key-Value", "duration_sec": 8, "on_screen_text": "Redis, DynamoDB, Memcached"},
        {"scene": 4, "title": "Document", "duration_sec": 8, "on_screen_text": "MongoDB, Cosmos DB, Couchbase"},
        {"scene": 5, "title": "Outro", "duration_sec": 8, "on_screen_text": "Subscribe for more system design"},
    ]
    with storyboard_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["scene", "title", "duration_sec", "on_screen_text"])
        writer.writeheader()
        writer.writerows(rows)

    readme = project_dir / "README.txt"
    readme.write_text(
        "Template created.\n\n"
        "Next steps:\n"
        "1) Replace slides in slides/ with your real exported slides.\n"
        "2) Add optional voice files in audio/ named scene_01.mp3, scene_02.mp3, ...\n"
        "3) Add optional background music at music/bgm.mp3\n"
        "4) Run:\n"
        f"   python {Path(__file__).name} --project {project_dir} --output {project_dir / 'output' / 'final.mp4'}\n",
        encoding="utf-8"
    )
    print(f"Template created at: {project_dir.resolve()}")


def find_first_matching_audio(audio_dir: Path, stem: str) -> Optional[Path]:
    for ext in SUPPORTED_AUDIO_EXTS:
        p = audio_dir / f"{stem}{ext}"
        if p.exists():
            return p
    return None


def list_scene_images(slides_dir: Path) -> List[Path]:
    imgs = [p for p in slides_dir.iterdir() if p.suffix.lower() in SUPPORTED_IMAGE_EXTS]
    # Sort by filename, assuming scene_01.png style
    return sorted(imgs, key=lambda p: p.name)


def read_storyboard(path: Path) -> Dict[int, Dict[str, str]]:
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    out: Dict[int, Dict[str, str]] = {}
    for _, row in df.iterrows():
        scene_num = int(row["scene"])
        out[scene_num] = {k: ("" if pd.isna(v) else str(v)) for k, v in row.to_dict().items()}
    return out


def fit_image_to_canvas(image_path: Path, width: int, height: int) -> Tuple[int, int]:
    with Image.open(image_path) as img:
        iw, ih = img.size
    scale = max(width / iw, height / ih)
    return int(iw * scale), int(ih * scale)


def make_zoom_clip(
    image_path: Path,
    duration: float,
    width: int,
    height: int,
    zoom_mode: str,
    crossfade: float,
    scene_idx: int,
) -> ImageClip:
    scaled_w, scaled_h = fit_image_to_canvas(image_path, width, height)

    # Static zoom scale (Ken Burns animation requires a custom VideoClip in v2;
    # a fixed slightly-oversized scale gives a comparable "zoomed" look)
    if zoom_mode == "none":
        scale = 1.0
    elif zoom_mode in ("in", "out"):
        scale = 1.08
    else:  # alternate
        scale = 1.08 if scene_idx % 2 == 1 else 1.0

    clip = (
        ImageClip(str(image_path))
        .resized((int(scaled_w * scale), int(scaled_h * scale)))
        .with_duration(duration)
        .with_position("center")
    )
    if crossfade > 0:
        clip = clip.with_effects([CrossFadeIn(crossfade)])
    return clip


def _get_font(size: int) -> ImageFont.FreeTypeFont:
    for path in [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _wrap(text: str, font: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    dummy = Image.new("RGBA", (1, 1))
    d = ImageDraw.Draw(dummy)
    words, lines, cur = text.split(), [], ""
    for word in words:
        test = (cur + " " + word).strip()
        if d.textbbox((0, 0), test, font=font)[2] <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def build_text_overlay(
    text: str,
    duration: float,
    width: int,
    height: int,
    font: str,          # kept for API compatibility, unused (uses system font)
    subtitle_size: int,
    bottom_margin: int,
):
    if not text.strip():
        return None

    import numpy as np

    max_text_w = int(width * 0.82)
    fnt = _get_font(subtitle_size)
    lines = _wrap(text, fnt, max_text_w)

    # Measure total text block height
    dummy_img = Image.new("RGBA", (1, 1))
    dummy_draw = ImageDraw.Draw(dummy_img)
    line_h = max((dummy_draw.textbbox((0, 0), ln, font=fnt)[3] for ln in lines), default=subtitle_size)
    block_h = line_h * len(lines) + 8 * len(lines)

    # Draw onto a transparent canvas sized to the full frame
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    y = height - bottom_margin - block_h
    for line in lines:
        line_w = draw.textbbox((0, 0), line, font=fnt)[2]
        x = (width - line_w) // 2
        # Shadow
        draw.text((x + 2, y + 2), line, font=fnt, fill=(0, 0, 0, 200))
        draw.text((x, y), line, font=fnt, fill=(255, 255, 255, 255))
        y += line_h + 8

    arr = np.array(img)
    clip = ImageClip(arr, is_mask=False).with_duration(duration).with_position((0, 0))
    return clip


def get_scene_number_from_name(path: Path) -> Optional[int]:
    stem = path.stem
    digits = "".join(ch for ch in stem if ch.isdigit())
    if digits:
        return int(digits)
    return None


def resolve_scene_duration(
    scene_num: int,
    audio_path: Optional[Path],
    storyboard_row: Dict[str, str],
    default_duration: float,
    scene_padding: float,
) -> Tuple[float, Optional[AudioFileClip]]:
    if audio_path and audio_path.exists():
        audio_clip = AudioFileClip(str(audio_path))
        return max(audio_clip.duration + scene_padding, 0.5), audio_clip

    if storyboard_row:
        try:
            d = float(storyboard_row.get("duration_sec", default_duration))
            return max(d, 0.5), None
        except Exception:
            pass

    return max(default_duration, 0.5), None


def build_video(
    project_dir: Path,
    output_path: Path,
    fps: int,
    width: int,
    height: int,
    default_duration: float,
    scene_padding: float,
    crossfade: float,
    music_volume: float,
    voice_volume: float,
    zoom_mode: str,
    font: str,
    subtitle_size: int,
    bottom_margin: int,
) -> None:
    slides_dir = project_dir / "slides"
    audio_dir = project_dir / "audio"
    music_dir = project_dir / "music"
    storyboard_path = project_dir / "storyboard.csv"

    if not slides_dir.exists():
        raise FileNotFoundError(f"Slides folder not found: {slides_dir}")

    images = list_scene_images(slides_dir)
    if not images:
        raise FileNotFoundError(f"No slide images found in: {slides_dir}")

    storyboard = read_storyboard(storyboard_path)

    scene_clips = []
    voice_audio_tracks = []

    for idx, image_path in enumerate(images, start=1):
        scene_num = get_scene_number_from_name(image_path) or idx
        row = storyboard.get(scene_num, {})
        audio_path = find_first_matching_audio(audio_dir, image_path.stem) if audio_dir.exists() else None
        duration, audio_clip = resolve_scene_duration(
            scene_num, audio_path, row, default_duration, scene_padding
        )

        base = make_zoom_clip(
            image_path=image_path,
            duration=duration,
            width=width,
            height=height,
            zoom_mode=zoom_mode,
            crossfade=crossfade,
            scene_idx=idx,
        )

        clips = [base]

        overlay_text = row.get("on_screen_text", "")
        txt_clip = build_text_overlay(
            text=overlay_text,
            duration=duration,
            width=width,
            height=height,
            font=font,
            subtitle_size=subtitle_size,
            bottom_margin=bottom_margin,
        )
        if txt_clip is not None:
            clips.append(txt_clip)

        comp = CompositeVideoClip(clips, size=(width, height)).with_duration(duration)

        if audio_clip is not None:
            audio_clip = audio_clip.multiply_volume(voice_volume)
            comp = comp.with_audio(audio_clip)
            voice_audio_tracks.append(audio_clip)

        scene_clips.append(comp)

    final = concatenate_videoclips(scene_clips, method="compose", padding=-crossfade if crossfade > 0 else 0)

    # Optional background music
    bgm_path = None
    if music_dir.exists():
        for ext in SUPPORTED_AUDIO_EXTS:
            candidate = music_dir / f"bgm{ext}"
            if candidate.exists():
                bgm_path = candidate
                break

    audio_layers = []
    if final.audio is not None:
        audio_layers.append(final.audio)

    if bgm_path is not None:
        bgm = AudioFileClip(str(bgm_path))
        if bgm.duration < final.duration:
            loops = int(math.ceil(final.duration / bgm.duration))
            bgm = concatenate_audio_loop(bgm, loops)
        bgm = bgm.subclipped(0, final.duration).multiply_volume(music_volume)
        audio_layers.append(bgm)

    if audio_layers:
        mixed = CompositeAudioClip(audio_layers)
        final = final.with_audio(mixed)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    final.write_videofile(
        str(output_path),
        fps=fps,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
        threads=os.cpu_count() or 4,
    )

    # Cleanup clips
    try:
        final.close()
    except Exception:
        pass
    for c in scene_clips:
        try:
            c.close()
        except Exception:
            pass


def concatenate_audio_loop(audio_clip: AudioFileClip, loops: int):
    from moviepy import concatenate_audioclips
    return concatenate_audioclips([audio_clip] * loops)


def main() -> None:
    args = parse_args()

    if args.init_template:
        create_template(Path(args.init_template))
        return

    if not args.project:
        raise SystemExit("Provide --project or use --init-template first.")
    if not args.output:
        raise SystemExit("Provide --output.")

    build_video(
        project_dir=Path(args.project),
        output_path=Path(args.output),
        fps=args.fps,
        width=args.width,
        height=args.height,
        default_duration=args.default_duration,
        scene_padding=args.scene_padding,
        crossfade=args.crossfade,
        music_volume=args.music_volume,
        voice_volume=args.voice_volume,
        zoom_mode=args.zoom_mode,
        font=args.font,
        subtitle_size=args.subtitle_size,
        bottom_margin=args.bottom_margin,
    )


if __name__ == "__main__":
    main()
