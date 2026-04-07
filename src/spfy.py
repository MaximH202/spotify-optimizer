import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

def auth_management():
    load_dotenv()
    auth_manager = SpotifyOAuth(
        scope="playlist-modify-public",
        open_browser= True
        )
    
    return auth_manager

def spotify_pull_data(playlist_id: str):
    load_dotenv()

    scope = "user-library-read"
    tracks = []

    sp = spotipy.Spotify(auth_manager= auth_management())

    results = sp.playlist_items(playlist_id)

    for idx, item in enumerate(results['items']):
        track = item['item']
        tracks.append({"idx": idx, "artist": track['artists'][0]['name'], "track_name": track['name']})

    return tracks

def spotify_push_data(new_tracks: list):
    #todo
    return
