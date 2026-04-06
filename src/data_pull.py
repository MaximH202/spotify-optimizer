import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import json
load_dotenv()

scope = "user-library-read"
tracks = []
music_dict = {}

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

results = sp.playlist_items("6TEtUXHUQkQAs2whkLzzlY")

for idx, item in enumerate(results['items']):
    track = item['item']
    tracks.append({"idx": idx, "artist": track['artists'][0]['name'], "track_name": track['name']})