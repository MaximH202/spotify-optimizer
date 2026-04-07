from spfy import spotify_pull_data, auth_management
from prompt_gen import generate_prompt
from ai_optimizer import playlist_opt
import json
import streamlit as st

st.title("Spotify Playlist Optimizer")

#Eingaben
response_url = st.text_input("Redirect-URL einfügen")
playlist_id = st.text_input("Playlist ID") #Test Playlist: "6TEtUXHUQkQAs2whkLzzlY"
playlist_vibe = st.text_input("Playlist Vibe | Optional")
anzahl_neuer_songs = st.number_input("Anzahl neuer Songs", min_value=1, max_value=20)
grenze_gelöschter_songs = st.number_input("Anzahl gelöschter Songs", min_value=0, max_value=20)
if 'key' not in st.session_state:
    st.session_state.key = 'value'


#Durchführung
if st.button("Spotify verbinden"):
    #Spotify Auth
    auth_manager= auth_management()
    auth_url = auth_manager.get_authorize_url()
    st.markdown(f"[Klick hier um dich zu verbinden]({auth_url})")
    st.session_state["auth_manager"] = auth_manager

elif st.button("Optimieren"):
    auth_manager = st.session_state.get("auth_manager")
    #Prompt Generierung und AI-Optimierung
    tracks = spotify_pull_data(playlist_id)
    opt_prompt = generate_prompt(tracks, anzahl_neuer_songs, grenze_gelöschter_songs, playlist_vibe)
    data = playlist_opt(opt_prompt)
    clean = data.text.strip().removeprefix("```json").removesuffix("```").strip()
    data = json.loads(clean)
    
    #Darstellung
    st.subheader("Entfernte Songs")
    st.dataframe(data["removed_songs"])

    st.subheader("Entfernte Songs")
    st.dataframe(data["added_songs"])

    st.subheader("Entfernte Songs")
    st.dataframe(data["final_playlist"])