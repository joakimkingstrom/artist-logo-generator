import os
import requests
import re
from plexapi.server import PlexServer

PLEX_URL = os.environ.get('PLEX_URL')
PLEX_TOKEN = os.environ.get('PLEX_TOKEN')
FANART_API_KEY = os.environ.get('FANART_API_KEY')
BASE_OUTPUT_DIR = '/app/ArtistLogos'

try:
    server = PlexServer(PLEX_URL, PLEX_TOKEN)
except Exception as e:
    print(f"Plex Connection Error: {e}")
    server = None


def get_library(name):
    return server.library.section(name) if server else None


def fetch_artist(rating_key):
    return server.fetchItem(int(rating_key)) if server else None


def get_artist_path(title):
    clean = re.sub(r'[\\/*?:"<>|]', "", title).strip()
    return os.path.join(BASE_OUTPUT_DIR, clean)


def get_fanart_logos(artist_obj):
    try:
        mbid = next((g.id.split('://')[-1] for g in artist_obj.guids if 'mbid' in g.id), None)
    except Exception:
        mbid = None
    if not mbid or not FANART_API_KEY:
        return []
    url = f"https://webservice.fanart.tv/v3/music/{mbid}?api_key={FANART_API_KEY}"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            return [l['url'] for l in (data.get('hdmusiclogo', []) + data.get('musiclogo', []))]
    except Exception:
        pass
    return []


def resource_to_url(val):
    """Convert a Plex resource (string, object, or attribute) to an absolute URL.

    Returns None when a usable URL cannot be derived.
    """
    if not val:
        return None

    # If it's already a string
    if isinstance(val, str):
        v = val.strip()
        if v.lower().startswith('http://') or v.lower().startswith('https://'):
            return v
        # relative Plex path
        if v.startswith('/') and server:
            try:
                return server.url(v, includeToken=True)
            except Exception:
                return v
        return v

    # If plexapi resource / object, prefer server.url
    try:
        if server:
            return server.url(val, includeToken=True)
    except Exception:
        pass

    # Fallback to common attributes
    for attr in ('key', 'thumb', 'url'):
        v = getattr(val, attr, None)
        if not v:
            continue
        if isinstance(v, str):
            if v.lower().startswith('http://') or v.lower().startswith('https://'):
                return v
            if server:
                try:
                    return server.url(v, includeToken=True)
                except Exception:
                    return v
            return v
        else:
            try:
                if server:
                    return server.url(v, includeToken=True)
            except Exception:
                try:
                    return str(v)
                except Exception:
                    return None

    try:
        return str(val)
    except Exception:
        return None


def get_artist_posters(artist_obj):
    """Return a best-effort list of poster/artwork URLs for an artist object."""
    posters = []
    if not artist_obj:
        return posters

    try:
        # Try posters() if available
        try:
            p = artist_obj.posters()
            if isinstance(p, dict):
                for _, v in p.items():
                    u = resource_to_url(v)
                    if u:
                        posters.append(u)
            elif isinstance(p, list):
                for v in p:
                    u = resource_to_url(v)
                    if u:
                        posters.append(u)
        except Exception:
            pass

        # Common fallback attributes
        if getattr(artist_obj, 'thumb', None):
            u = resource_to_url(artist_obj.thumb)
            if u:
                posters.append(u)

        if getattr(artist_obj, 'art', None):
            u = resource_to_url(artist_obj.art)
            if u:
                posters.append(u)

        # Sometimes media entries contain artwork
        if getattr(artist_obj, 'media', None):
            for m in artist_obj.media:
                if getattr(m, 'thumb', None):
                    u = resource_to_url(m.thumb)
                    if u:
                        posters.append(u)
    except Exception as e:
        print(f"get_artist_posters error: {e}")

    # Deduplicate while preserving order
    seen = set()
    out = []
    for u in posters:
        if not u:
            continue
        if u in seen:
            continue
        seen.add(u)
        out.append(u)
    return out