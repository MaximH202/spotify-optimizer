import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

def spotify_data(playlist_id: str):
    load_dotenv()

    scope = "user-library-read"
    tracks = []

    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

    results = sp.playlist_items(playlist_id)

    for idx, item in enumerate(results['items']):
        track = item['item']
        tracks.append({"idx": idx, "artist": track['artists'][0]['name'], "track_name": track['name']})

    return tracks