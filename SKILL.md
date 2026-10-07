---
name: gemini-veo-studio
description: Make short videos with Google Veo (Gemini API) from Claude. Opens a starter panel of video templates like the Gemini app, writes the prompt, generates clips with sound, then optionally finishes them in code (mascot swap, phone screens, captions, end card).
---

# Gemini Veo Studio Skill for Claude

Claude plans and finishes; Veo films. Veo runs through the official Gemini API with the user's own key, so this works anywhere Claude has a shell (Claude Code, or a linked computer).

## 0. Setup (once)
- `pip install google-genai`
- The user needs an API key from https://aistudio.google.com/apikey, exported as `GEMINI_API_KEY`. Never print, log or commit the key; ask the user to set it in their own shell.
- Veo is not on the Gemini API free tier: it is billed per second of video on the user's Google account, and a Gemini app subscription does not cover it. Say this once before the first generation, with the prices in README.md. Check current prices at https://ai.google.dev/gemini-api/docs/pricing.
- If the network blocks generativelanguage.googleapis.com, run the script on the user's machine instead.

## 1. Show the starter panel first
When the user asks for a video and has no clear brief, show the panel before writing prompts:
- Run `python3 scripts/panel.py` and open or send `panel.html`. It is a gallery of templates (Creators, Brand, Restyle, Celebration), like the Videos page in the Gemini app. `--thumbs` makes real thumbnails with Gemini's image model, which is billed.
- In chat, offer the same choice with the question tool: first the category, then up to 4 templates from it. A free-text answer always works.
- Templates live in `assets/templates.json`. Each has `{placeholders}` (subject, place, line, name), the input it needs, and a default aspect. Add new templates there.

## 2. Write the shot list
- One Veo call = one shot of 4, 6 or 8 s. Plan 3 to 5 shots for a 15 to 40 s video.
- Prompt rules that work:
  - say the camera (locked-off, push-in, handheld);
  - say the light and the look;
  - put dialogue in double quotes;
  - describe sounds;
  - end with "No on-screen text" (Veo text comes out garbled; add text in edit).
- Same character in every shot: describe it identically, or pass up to 3 `--ref` images (8 s only).
- A phone or screen that will show a real UI: locked-off camera and a "flat solid chroma-key green" screen, so it can be replaced in edit.
- Save the shot list as a .md and show it before spending money on generation.

## 3. Generate
```
python3 scripts/veo.py "<prompt>" -o shot1.mp4 [--aspect 9:16] [--seconds 8] [--resolution 1080p]
python3 scripts/veo.py --template talking-pet --set subject="a cream cat" --set line="Hi!" -o pet.mp4
python3 scripts/veo.py "<prompt>" --ref mascot.png -o intro.mp4         # keep a character or product
python3 scripts/veo.py "<prompt>" --first a.png --last b.png -o x.mp4    # first and last frame
python3 scripts/veo.py "<prompt>" --extend shot1.json -o shot1b.mp4      # continue a clip (+7 s, 720p)
python3 scripts/veo.py --list | --dry-run
```
- Each run takes about 1 to 6 minutes.
- It saves the .mp4 and a .json with the request and the video URI. Extension needs that URI, and Google keeps generated videos for 2 days.
- In the EU, UK, CH and MENA, people generation is limited to adults.
- A clip blocked by safety filters returns no video and is not billed. Rephrase the prompt and retry once.
- Generate shots one at a time and look at each one: make a contact sheet with ffmpeg and read it before moving on.

## 4. Finish in code (optional, this is where Claude adds the most)
See `references/post-production.md`:
- join the shots;
- keep Veo's own audio;
- swap a stand-in character for the real mascot, with the mouth driven by the audio;
- replace green screens with a rendered UI flow;
- clean garbled text;
- add captions and an end card;
- export H.264.

## 5. Deliver
- Send the final .mp4 and say what is generated and what was added in edit.
- Mark example or illustrative numbers in the video itself.
- Do not claim a real person or brand endorsed it.
