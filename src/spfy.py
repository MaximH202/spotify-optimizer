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

    results = sp.playlist_items(playlist_id)

    for idx, item in enumerate(results['items']):
        track = item['item']
        tracks.append({"idx": idx, "artist": track['artists'][0]['name'], "track_name": track['name']})

    return tracks

def spotify_push_data(new_tracks: list, Playlist_Name: str, auth_manager=None):
    load_dotenv()
    if auth_manager is None:
        auth_manager = auth_management()
    sp = spotipy.Spotify(auth_manager=auth_manager)
    #Neu erstellte Playlist
    playlist = sp.current_user_playlist_create(Playlist_Name, public=True, collaborative=False, description='Your new Playlist, optimized by AI')
    
    sp.playlist_add_items(playlist["id"], get_uri(new_tracks, auth_manager), position=None)

def get_uri(new_tracks: list, auth_manager=None):
    load_dotenv()
    sp = spotipy.Spotify(auth_manager=auth_manager)
    track_name = [song["track_name"] for song in new_tracks["final_playlist"]]
    artist_name = [song["artist"] for song in new_tracks["final_playlist"]]
    uri_list= []

    #URI der Lieder aus new_tracks ermitteln
    for i in range(0, len(new_tracks["final_playlist"])):
        q= f"remaster track:{track_name[i]} artist:{artist_name[i]}"
        result = sp.search(q, limit=1, offset=0, type='track', market=None)
        uri_list.append(result["tracks"]["items"][0]["uri"])

    return uri_list