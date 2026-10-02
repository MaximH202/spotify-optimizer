import spotipy
# pyrefly: ignore [missing-import]
from spotipy.oauth2 import SpotifyOAuth
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
import re

def extract_playlist_id(playlist_input: str) -> str:
    """Extrahiert eine saubere Spotify-Playlist-ID aus einer ID, URI oder URL."""
    if not playlist_input:
        return ""
    clean_input = playlist_input.strip()

    # Fall: si= Parameter versehentlich kopiert
    if clean_input.startswith("?si=") or clean_input.startswith("si="):
        clean_input = clean_input.split("=")[-1].strip()

    # Spotify URL prüfen (z. B. https://open.spotify.com/playlist/6TEtUXHUQkQAs2whkLzzlY?si=...)
    url_match = re.search(r"open\.spotify\.com(?:/intl-[a-z]{2})?/playlist/([a-zA-Z0-9]+)", clean_input)
    if url_match:
        return url_match.group(1)

    # Spotify URI prüfen (z. B. spotify:playlist:6TEtUXHUQkQAs2whkLzzlY)
    uri_match = re.search(r"spotify:playlist:([a-zA-Z0-9]+)", clean_input)
    if uri_match:
        return uri_match.group(1)

    # (Der Check auf 16-stellige Hex-Strings wurde entfernt, da manche echte Playlists 16-stellige IDs haben)

    return clean_input

#Auth_manager initialisieren
def auth_management():
    load_dotenv()
    auth_manager = SpotifyOAuth(
        scope="playlist-modify-public playlist-modify-private user-library-read",
        open_browser=False
    )
    return auth_manager

#Spotify Auth und Datenabruf
def spotify_pull_data(playlist_id: str, auth_manager=None):
    load_dotenv()

    playlist_id = extract_playlist_id(playlist_id)
    tracks = []

    if auth_manager is None:
        auth_manager = auth_management()

    sp = spotipy.Spotify(auth_manager=auth_manager)

    results = sp.playlist_items(playlist_id, limit = 100)
    while results:
    #Liste der Songs aus Spotify abrufen und prüfen ob Daten vorhanden sind
        for item in results.get('items', []):
            track = item.get('track') or item.get('item')
            if not track:
                continue
            artists = track.get('artists')
            if not artists:
                continue
            tracks.append({
                "idx": len(tracks), 
                "artist": artists[0]['name'], 
                "track_name": track.get('name', 'Unbekannt')
            })
        results = sp.next(results) if results.get('next') else None
    return tracks

#Spotify Push Playlist
def spotify_push_data_new_playlist(data: dict, Playlist_Name: str, auth_manager=None):
    load_dotenv()
    if auth_manager is None:
        auth_manager = auth_management()
    sp = spotipy.Spotify(auth_manager=auth_manager)
    
    # Playlist-Name Standardwert falls leer
    if not Playlist_Name:
        Playlist_Name = "AI Optimized Playlist"
        
    try:
        # Neu erstellte Playlist
        playlist = sp.current_user_playlist_create(
            Playlist_Name, 
            public=True, 
            collaborative=False, 
            description='Your new Playlist, optimized by AI'
        )
        
        uris = get_uri(data, auth_manager)
        if uris:
            sp.playlist_add_items(playlist["id"], uris, position=None)
        return playlist
    except spotipy.SpotifyException as e:
        print(f"Spotify API Fehler: {e}")
        raise e

#Uri's der einzelnen Lieder ermitteln, da Spotify die ID des Songs und nicht den Song selbst benötigt
def get_uri(data: dict, auth_manager=None):
    load_dotenv()
    sp = spotipy.Spotify(auth_manager=auth_manager)
    
    final_playlist = data.get("final_playlist", [])
    uri_list = []

    # URI der Lieder aus final_playlist ermitteln
    for song in final_playlist:
        track_name = song.get("track_name")
        artist_name = song.get("artist")
        
        # Suche ohne "remaster" für bessere Ergebnisse
        q = f"track:{track_name} artist:{artist_name}"
        result = sp.search(q, limit=1, type='track')
        
        tracks = result.get("tracks", {}).get("items", [])
        if tracks:
            uri_list.append(tracks[0]["uri"])
        else:
            # Fallback: Suche nur nach Track-Name falls Künstler-Kombination nichts findet
            q_fallback = f"track:{track_name}"
            result_fallback = sp.search(q_fallback, limit=1, type='track')
            tracks_fallback = result_fallback.get("tracks", {}).get("items", [])
            if tracks_fallback:
                uri_list.append(tracks_fallback[0]["uri"])
            else:
                print(f"Song nicht gefunden: {track_name} von {artist_name}")

    return uri_list

#Playlist aktualisieren
def update_playlist(playlist_id: str, data: dict, auth_manager=None):
    load_dotenv()
    playlist_id = extract_playlist_id(playlist_id)
    sp = spotipy.Spotify(auth_manager=auth_manager)
    uris = get_uri(data, auth_manager)
    sp.playlist_replace_items(playlist_id, items=uris)
