
# Optional local workflow with FFmpeg (not required)

If you want to assemble a simple video locally:
1. Create images/slides for each scene using Canva exports or screenshots.
2. Record voiceover scene by scene.
3. Put scene images into /assets/images
4. Put audio files into /assets/audio
5. Use FFmpeg to create one clip per scene and concat them.

This generator does not create FFmpeg commands automatically because your exported file names will vary.
But your folder structure is ready for it.

Suggested naming:
images/scene_01.png
audio/scene_01.mp3
...
