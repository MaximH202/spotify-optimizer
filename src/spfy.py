import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

def auth_management():
    load_dotenv()
    auth_manager = SpotifyOAuth(
        scope="playlist-modify-public user-library-read",
        open_browser=False
    )
    return auth_manager

def spotify_pull_data(playlist_id: str, auth_manager=None):
    load_dotenv()

    tracks = []

    if auth_manager is None:
        auth_manager = auth_management()

    sp = spotipy.Spotify(auth_manager=auth_manager)

    results = sp.playlist_items(playlist_id, limit=75)

    for idx, item in enumerate(results['items']):
        track = item['item']
        tracks.append({"idx": idx, "artist": track['artists'][0]['name'], "track_name": track['name']})

    return tracks

def spotify_push_data(data: dict, Playlist_Name: str, auth_manager=None):
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
            # Spotify allows adding max 100 items at a time
            sp.playlist_add_items(playlist["id"], uris, position=None)
        return playlist
    except spotipy.SpotifyException as e:
        print(f"Spotify API Fehler: {e}")
        raise e

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
