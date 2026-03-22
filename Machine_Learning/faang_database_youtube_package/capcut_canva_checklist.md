
# Free-tool workflow for this YouTube video

## Recommended free online tools
1. **Canva Video Editor**
   - Use for slide-based visuals, captions, simple animations, and assembling the full video.
   - Create a 1920x1080 video project.
   - Copy each scene's on-screen text and voiceover into separate pages.

2. **CapCut Online**
   - Use if you want faster timeline editing, auto-captions, transitions, zoom effects, and easier B-roll handling.
   - Import your stock footage, voiceover, and scene text.

3. **Pexels**
   - Use for free stock videos/images relevant to tech, servers, networking, data centers, cloud animation, dashboards.

4. **Pixabay**
   - Use when Pexels does not have a suitable stock clip or icon-like footage.

## Suggested production workflow
### Option A — Canva-first workflow
1. Run this Python script.
2. Open `storyboard.csv`.
3. Create one Canva page per scene.
4. For each scene:
   - put the on-screen text as headline
   - paste or record the voiceover
   - add 1–3 stock visuals using `assets_to_download.csv`
   - animate text lightly
5. Add background music at very low volume.
6. Export as 1080p MP4.
7. Upload to YouTube Studio using `youtube_metadata.md`.

### Option B — CapCut-first workflow
1. Run this Python script.
2. Record voiceover using `narration_chunks.txt`.
3. Download clips listed in `assets_to_download.csv`.
4. Import voiceover + clips into CapCut Online.
5. Build the timeline scene by scene using `storyboard.csv`.
6. Add subtitles from the voiceover.
7. Export as 1080p or 4K MP4.
8. Upload to YouTube.

## Free production checklist
- [ ] Create 16:9 project
- [ ] Keep total runtime around 8–10 minutes
- [ ] Use large readable titles
- [ ] Keep 1 idea per scene
- [ ] Add subtle zoom/pan to static visuals
- [ ] Add subtitles
- [ ] Use royalty-free visuals only
- [ ] Check pronunciation of product names
- [ ] Export 1080p MP4
- [ ] Upload thumbnail + metadata

## Thumbnail plan
Big text options:
- FAANG Database Designs
- 25 Databases Explained
- System Design Databases
- Redis vs Mongo vs Cassandra

Visual idea:
- dark tech background
- 4–6 database logos
- arrows between app, cache, DB, analytics
