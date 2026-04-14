import spotipy
from spfy import spotify_pull_data
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
load_dotenv()

auth_manager = SpotifyOAuth(
        scope="playlist-modify-public user-library-read",
        open_browser=False
    )

sp = spotipy.Spotify(auth_manager=auth_manager)
#Neu erstellte Playlist
data= spotify_pull_data("6TEtUXHUQkQAs2whkLzzlY", auth_manager)
print(data)
    
#sp.playlist_add_items(playlist["id"], get_uri(new_tracks, auth_manager), position=None)