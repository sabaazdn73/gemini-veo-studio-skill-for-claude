# Finishing Veo clips in code

Tools: ffmpeg, Python with numpy, opencv-python and Pillow, and Playwright for rendering HTML to transparent PNGs.

## Inspect
- `ffprobe` each clip. Veo clips are 24 fps and carry an AAC audio track.
- Contact sheet: `ffmpeg -i in.mp4 -vf "fps=4,scale=320:-1,tile=8x5" -frames:v 1 sheet.png`.
- Cuts: frame-to-frame mean absolute difference above ~30. Letterbox or camcorder frames: a dark left border.

## Keep the audio
Map the original audio (`-map 1:a`), pad with `apad`, and fade out before an end card. Do not swap in music unless asked. If you replace a shot, keep its length so the voice stays in sync.

## Swap a stand-in character for the real mascot (2D puppet)
1. Clean plate from the first frame: fill the character's box by row interpolation between narrow bands either side of it. Blur the wall rows vertically, feather the edges and add a light overall blur for depth of field.
2. Mascot from a transparent PNG:
   - body layer = the image minus the head (soft edge);
   - head layer rotates a few degrees about the neck.
3. Motion:
   - slow camera push-in;
   - 2% squash/stretch with a small bob;
   - a blurred ellipse contact shadow.
4. Mouth: an ellipse under the nose whose opening follows the audio RMS per frame (16 kHz mono, window = 1/24 s).
5. Blinks: fur-coloured lids over the eyes for 2 to 3 frames.

Limits: no arm waves from a single image. For full motion, generate the shot with Veo using `--ref mascot.png`.

## Replace a green phone screen or add a floating phone
- Render each UI state as a transparent PNG with Playwright (`omit_background=True`), for example typing in 2-character steps, sent, typing dots, reply, cards, and buttons before and after being tapped.
- Composite per frame:
  - eased slide-in;
  - gentle float and rotation;
  - a blurred drop shadow;
  - 0.15 s crossfades between states;
  - a white ripple where a button is tapped.
- For a real green screen: key with HSV and warp the UI into the screen quad with `cv2.getPerspectiveTransform`.

## Clean model text
Mask bright text pixels in the box, `cv2.inpaint`, then draw clean text with Pillow (for example a REC label with a running timecode).

## End card
A gradient background, logo or mascot, name, a one-line tagline and the URL. Add "Example figures" whenever the numbers are illustrative. Crossfade in with a slow 3% zoom.

## Export
Pipe raw RGB frames to ffmpeg: `-c:v libx264 -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart`. Upscale 720p sources to 1080p with cubic interpolation and a light unsharp mask.
