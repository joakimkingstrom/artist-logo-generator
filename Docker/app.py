import os, base64, re, requests, json
from flask import Flask, render_template, request, jsonify, send_file
from io import BytesIO
from PIL import ImageFont
import plex_utils, logic

app = Flask(__name__)

def load_default_fonts():
    """Loads default fonts from fonts.txt, with a fallback list."""
    try:
        with open('fonts.txt', 'r') as f:
            return [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
    except FileNotFoundError:
        print("Warning: fonts.txt not found. Using a hardcoded fallback list.")
        return [
            "Roboto", "Open Sans", "Lato", "Montserrat", "Oswald", "Raleway", "Merriweather", 
            "Pacifico", "Dancing Script", "Bebas Neue", "Anton", "Lobster", "Comfortaa",
            "Cinzel", "Fauna One", "Orbitron", "Press Start 2P", "Special Elite"
        ]

DEFAULT_FONTS = load_default_fonts()

@app.route('/')
def index():
    lib = plex_utils.get_library(os.environ.get('LIBRARY_NAME', 'Music'))
    artists = sorted(lib.all(), key=lambda x: re.sub(r'^(the|a|an)\s+', '', x.title.lower()))
    
    data = []
    for a in artists:
        path = plex_utils.get_artist_path(a.title)
        status_file = os.path.join(path, '.status')
        status = 'none'
        if os.path.exists(status_file):
            with open(status_file, 'r') as f:
                status = f.read().strip()
        data.append({'obj': a, 'status': status})
    return render_template('index.html', artists=data, fonts=DEFAULT_FONTS)

def download_font_if_needed(font_name):
    """Checks if a font is available locally, and if not, downloads it from Google Fonts."""
    # Let's not assume ttf. We'll check for any valid font file.
    font_basename = f"{font_name.replace(' ', '')}-Regular"
    font_dir = logic.FONT_DIR
    
    # Check if a font file exists (with any supported extension)
    for ext in ['.ttf', '.otf', '.woff', '.woff2']:
        f_path = os.path.join(font_dir, font_basename + ext)
        if os.path.exists(f_path):
            return f_path

    print(f"Font '{font_name}' not found locally. Attempting to download from Google Fonts...")

    try:
        css_url = f"https://fonts.googleapis.com/css2?family={font_name.replace(' ', '+')}:wght@400&display=swap"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        }
        css_response = requests.get(css_url, headers=headers)
        css_response.raise_for_status()
        css_text = css_response.text

        # Find all font URLs
        font_urls = re.findall(r"url\((http.*?)\)", css_text)
        if not font_urls:
            print(f"Could not find any font URL in the CSS for '{font_name}'.")
            return None

        # Prefer ttf, but take what we can get. Let's try to find a URL for the 'latin' subset if possible.
        # This is tricky because there are multiple font-face declarations.
        # For simplicity, let's just take the last URL, which is often the one for the basic latin set.
        font_url = font_urls[-1]

        # Determine file extension
        extension = ".ttf" # default
        if ".woff2" in font_url:
            extension = ".woff2"
        elif ".woff" in font_url:
            extension = ".woff"
        elif ".otf" in font_url:
            extension = ".otf"

        font_filename = font_basename + extension
        f_path = os.path.join(font_dir, font_filename)

        font_response = requests.get(font_url)
        font_response.raise_for_status()

        os.makedirs(font_dir, exist_ok=True)
        with open(f_path, 'wb') as f:
            f.write(font_response.content)

        print(f"Successfully downloaded and saved '{font_name}' to '{f_path}'.")
        return f_path

    except requests.exceptions.RequestException as e:
        print(f"Error downloading font '{font_name}': {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while downloading font '{font_name}': {e}")
        return None

@app.route('/get_options/<rating_key>')
def get_options(rating_key):
    artist = plex_utils.fetch_artist(rating_key)
    logos = plex_utils.get_fanart_logos(artist)
    return jsonify({"logos": logos, "google_url": f"https://www.google.com/search?q={artist.title}+transparent+logo+png&tbm=isch"})


@app.route('/get_posters/<rating_key>')
def get_posters(rating_key):
    artist = plex_utils.fetch_artist(rating_key)
    posters = plex_utils.get_artist_posters(artist)
    return jsonify({"posters": posters})


@app.route('/set_poster', methods=['POST'])
def set_poster():
    data = request.json or {}
    rating_key = data.get('rating_key')
    url = data.get('url')
    if not rating_key or not url:
        return jsonify({'status': 'error', 'message': 'rating_key and url required'}), 400

    artist = plex_utils.fetch_artist(rating_key)
    if not artist:
        return jsonify({'status': 'error', 'message': 'artist not found'}), 404

    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        # Save to a temporary file so plexapi can upload it
        import tempfile
        tf = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        tf.write(resp.content)
        tf.flush()
        tf.close()

        artist.uploadPoster(filepath=tf.name)

        try:
            os.remove(tf.name)
        except Exception:
            pass

        return jsonify({'status': 'success'})
    except Exception as e:
        print(f"set_poster error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/proxy_image')
def proxy_image():
    url = request.args.get('url')
    if not url:
        return 'url required', 400
    # Normalize input using plex_utils.resource_to_url which handles
    # absolute URLs, plex-relative paths and plexapi resource objects.
    try:
        normalized = plex_utils.resource_to_url(url)
    except Exception as e:
        print(f"proxy_image resource_to_url error for {url}: {e}")
        return jsonify({'status': 'error', 'message': 'invalid url'}), 400

    if not normalized or not (normalized.startswith('http://') or normalized.startswith('https://')):
        return 'invalid url', 400

    url = normalized

    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        ct = r.headers.get('Content-Type', 'image/jpeg') or r.headers.get('Content-Type') or 'application/octet-stream'
        return send_file(BytesIO(r.content), mimetype=ct)
    except Exception as e:
        print(f"proxy_image error fetching {url}: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 502

@app.route('/save', methods=['POST'])
def save():
    data = request.json
    artist = plex_utils.fetch_artist(data['rating_key'])
    if data['url'].startswith('data:image'):
        img = logic.Image.open(BytesIO(base64.b64decode(data['url'].split(',')[1])))
    else:
        img = logic.Image.open(BytesIO(requests.get(data['url']).content))
    
    final = logic.apply_transforms(img, **{k: data.get(k) for k in ['apply_default_size', 'invert', 'make_white', 'contrast', 'zoom', 'monochrome', 'tint']})
    path = plex_utils.get_artist_path(artist.title)
    os.makedirs(path, exist_ok=True)
    final.save(os.path.join(path, "artist.jpg"), "JPEG", quality=95)
    
    with open(os.path.join(path, '.status'), 'w') as f:
        f.write('done')

    if os.environ.get('UPDATE_PLEX', 'false').lower() == 'true': artist.uploadPoster(filepath=os.path.join(path, "artist.jpg"))
    return jsonify({"status": "success"})

@app.route('/save_custom', methods=['POST'])
def save_custom():
    data = request.json
    artist = plex_utils.fetch_artist(data['rating_key'])
    font_name = data.get('font', 'Roboto') # Default to Roboto

    f_path = download_font_if_needed(font_name)
    if not f_path:
        f_path = ImageFont.load_default()

    img = logic.generate_text_logo(artist.title, f_path, **{k: data.get(k) for k in ['rows', 'color', 'case']})
    path = plex_utils.get_artist_path(artist.title)
    os.makedirs(path, exist_ok=True)
    img.save(os.path.join(path, "artist.jpg"), "JPEG", quality=95)
    
    with open(os.path.join(path, '.status'), 'w') as f:
        f.write('custom')

    if os.environ.get('UPDATE_PLEX', 'false').lower() == 'true': artist.uploadPoster(filepath=os.path.join(path, "artist.jpg"))
    return jsonify({"status": "success"})

@app.route('/toggle_status/<rating_key>', methods=['POST'])
def toggle_status(rating_key):
    artist = plex_utils.fetch_artist(rating_key)
    path = plex_utils.get_artist_path(artist.title)
    os.makedirs(path, exist_ok=True)
    status_file = os.path.join(path, '.status')
    
    current_status = 'none'
    if os.path.exists(status_file):
        with open(status_file, 'r') as f:
            current_status = f.read().strip()
            
    if current_status == 'none':
        next_status = 'custom'
    elif current_status == 'custom':
        next_status = 'done'
    else: # done
        next_status = 'none'
        
    with open(status_file, 'w') as f:
        f.write(next_status)
        
    return jsonify({'status': 'success', 'new_status': next_status})

@app.route('/bulk_apply_fanart', methods=['POST'])
def bulk_apply_fanart():
    data = request.json
    artist_keys = data.get('artist_keys', [])
    updated_count = 0

    for key in artist_keys:
        try:
            artist = plex_utils.fetch_artist(key)
            logos = plex_utils.get_fanart_logos(artist)
            
            if logos:
                most_popular_logo_url = logos[0]
                
                img = logic.Image.open(BytesIO(requests.get(most_popular_logo_url).content))
                final = logic.apply_transforms(img, apply_default_size=True) # Using default sizing
                
                path = plex_utils.get_artist_path(artist.title)
                os.makedirs(path, exist_ok=True)
                final.save(os.path.join(path, "artist.jpg"), "JPEG", quality=95)
                
                if os.path.exists(os.path.join(path, ".custom")):
                    os.remove(os.path.join(path, ".custom"))
                
                if os.environ.get('UPDATE_PLEX', 'false').lower() == 'true':
                    artist.uploadPoster(filepath=os.path.join(path, "artist.jpg"))
                
                updated_count += 1
        except Exception as e:
            print(f"Error updating artist {key}: {e}")
            continue
            
    return jsonify({"status": "success", "updated_count": updated_count})

@app.route('/bulk_toggle_status', methods=['POST'])
def bulk_toggle_status():
    data = request.json
    artist_keys = data.get('artist_keys', [])
    updated_artists = []
    
    for key in artist_keys:
        try:
            artist = plex_utils.fetch_artist(key)
            path = plex_utils.get_artist_path(artist.title)
            os.makedirs(path, exist_ok=True)
            status_file = os.path.join(path, '.status')
            
            current_status = 'none'
            if os.path.exists(status_file):
                with open(status_file, 'r') as f:
                    current_status = f.read().strip()
            
            if current_status == 'none':
                next_status = 'custom'
            elif current_status == 'custom':
                next_status = 'done'
            else: # done
                next_status = 'none'
                
            with open(status_file, 'w') as f:
                f.write(next_status)
            
            updated_artists.append({'key': key, 'new_status': next_status})
        except Exception as e:
            print(f"Error updating artist {key}: {e}")
            continue
            
    return jsonify({"status": "success", "updated_count": len(updated_artists), "updated_artists": updated_artists})


@app.route('/preview_text', methods=['POST'])
def preview_text():
    data = request.json
    artist = plex_utils.fetch_artist(data['rating_key'])
    font_name = data.get('font', 'Roboto') # Default to Roboto

    f_path = download_font_if_needed(font_name)
    if not f_path:
        f_path = ImageFont.load_default()

    img = logic.generate_text_logo(artist.title, f_path, **{k: data.get(k) for k in ['rows', 'color', 'case']})
    
    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    return jsonify({"image": img_str})

@app.route('/plex_proxy/<rating_key>')
def plex_proxy(rating_key):
    artist = plex_utils.fetch_artist(rating_key)
    # Use plex_utils to convert artist.thumb into a usable URL
    try:
        thumb_url = plex_utils.resource_to_url(artist.thumb)

        if not thumb_url:
            return 'thumb not available', 404

        r = requests.get(thumb_url, timeout=15)
        r.raise_for_status()
        return send_file(BytesIO(r.content), mimetype=r.headers.get('Content-Type', 'image/jpeg'))
    except Exception as e:
        print(f"plex_proxy error: {e}")
        return 'error', 500

if __name__ == '__main__':
    # Download all fonts on startup
    print("Downloading all fonts listed in fonts.txt...")
    for font in DEFAULT_FONTS:
        download_font_if_needed(font)
    print("Font download process finished.")
    app.run(host='0.0.0.0', port=5000)