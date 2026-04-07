from data_pull import spotify_data
from prompt_gen import generate_prompt
from ai_optimizer import playlist_opt
import streamlit

anzahl_neuer_songs = 10
grenze_gelöschter_songs = 5
playlist_vibe = "Latenight Drive"
playlist_id = "6TEtUXHUQkQAs2whkLzzlY"

tracks = spotify_data(playlist_id)
opt_prompt = generate_prompt(tracks, anzahl_neuer_songs, grenze_gelöschter_songs, playlist_vibe)
data = playlist_opt(opt_prompt)

removed_songs = data["removed_songs"]
added_songs = data["added_songs"]
final_playlist = data["final_playlist"]

print(removed_songs)