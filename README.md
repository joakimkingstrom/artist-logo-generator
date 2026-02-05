# Plex Artist Logo Editor

A lightweight web UI and backend for browsing, editing and setting artist posters/logos in a Plex library.

This repository contains a Flask backend which interfaces with Plex and provides an editor UI for applying fanart/text-based logos, previewing transformations (invert/greyscale/tint/contrast/zoom), and saving results back to Plex.

![alt text](https://github.com/joakimkingstrom/artist-logo-generator/blob/main/screenshots/SCR-20260205-uggm.png)
![alt text](https://github.com/joakimkingstrom/artist-logo-generator/blob/main/screenshots/SCR-20260205-ugle.png)
![alt text](https://github.com/joakimkingstrom/artist-logo-generator/blob/main/screenshots/SCR-20260205-ugsl.png)

Key files
- `Docker/` – application source and Flask app (`app.py`, `logic.py`, `plex_utils.py`) and static assets.
- `Docker/templates/index.html` – main UI template.
- `Docker/static/js/` – frontend modules: `editor.js`, `colorpicker.js`, `preview.js`, `lightbox.js`.
- `Docker/static/css/` – styles: `base.css`, `editor.css`, `controls.css`, `lightbox.css`.
- `Docker/Dockerfile` – image build for the app.
- `compose.yaml` – optional compose definition.
- `.env.example` – environment variables file.

Quick start (Docker)

1. Build image (from repo root):

```bash
# from project root
docker build -t plex-artist-logos -f Docker/Dockerfile .
# or use compose if provided
docker compose up --build
```

2. Visit the app in your browser (default `http://localhost:5000` unless overridden by compose).

Important endpoints
- `/` – main UI.
- `/get_options/<rating_key>` – returns available fanart/logo images for an artist.
- `/get_posters/<rating_key>` – returns Plex poster resources for an artist.
- `/set_poster` – POST to set a poster for an artist in Plex (used by the lightbox "Use as artist image").
- `/preview_text` – generate preview for text-based logos.
- `/save` and `/save_custom` – save selected/generated logos back to Plex.
- `/proxy_image?url=...` – image proxy to avoid cross-origin issues.
- `/plex_proxy/<rating_key>` – proxy current artist image from Plex.

Editing the UI
- Frontend logic lives in `Docker/static/js/` and styles in `Docker/static/css/`.
- `templates/index.html` is the single page template; JS files are loaded at the bottom of the page.

Notes and troubleshooting
- The app normalises Plex resource URLs via `resource_to_url()` in `Docker/plex_utils.py`.
- If cross-origin image masking fails, check `/proxy_image` behaviour and ensure Plex URLs are accessible to the service.
- Use browser devtools network panel to inspect proxied image requests when debugging thumbnails or lightbox images.

Fonts
- The file `Docker/fonts.txt` lists font family names (one per line) used by the text-generator UI. Lines starting with `#` are treated as comments and ignored.
- Behaviour: on startup the app reads `fonts.txt` to populate the font selector and will attempt to download any missing fonts from Google Fonts (saved to the font directory used by `logic.py`). The download is best-effort — network access to Google Fonts is required and not all font families map cleanly to a single TTF/OTF/WOFF file.
- To add a font: add its Google Fonts family name to `Docker/fonts.txt` (one per line), then restart the service so the app can attempt to download it.

`Made together with Github copilot.`