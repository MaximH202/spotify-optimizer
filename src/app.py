from spfy import spotify_pull_data, spotify_push_data, auth_management
from prompt_gen import generate_prompt
from ai_optimizer import playlist_opt
import json
import streamlit as st
from google.genai.errors import ServerError
import os
from dotenv import load_dotenv

load_dotenv()

# Liste der benötigten Umgebungsvariablen
required_keys = ["SPOTIPY_CLIENT_ID", "SPOTIPY_CLIENT_SECRET", "SPOTIPY_REDIRECT_URI", "GOOGLE_API_KEY"]

# Überprüfen, ob Daten bereits vorhanden sind (in .env oder st.session_state)
def get_missing_keys():
    return [key for key in required_keys if not os.getenv(key) and key not in st.session_state]

missing_keys = get_missing_keys()

# Falls Daten fehlen -> Setup anzeigen
if missing_keys:
    st.title("⚙️ Setup")
    st.info("Bitte gib deine API-Daten ein. Sobald du speicherst, verschwindet dieses Menü.")
    
    spotify_id = st.text_input("Spotify Client ID", value=st.session_state.get("SPOTIPY_CLIENT_ID", ""))
    spotify_secret = st.text_input("Spotify Client Secret", type="password", value=st.session_state.get("SPOTIPY_CLIENT_SECRET", ""))
    spotify_uri = st.text_input("Spotify Redirect URI", value=st.session_state.get("SPOTIPY_REDIRECT_URI", ""))
    google_key = st.text_input("Google API Key", type="password", value=st.session_state.get("GOOGLE_API_KEY", ""))
    
    if st.button("Einstellungen speichern"):
        if spotify_id and spotify_secret and spotify_uri and google_key:
            st.session_state["SPOTIPY_CLIENT_ID"] = spotify_id
            st.session_state["SPOTIPY_CLIENT_SECRET"] = spotify_secret
            st.session_state["SPOTIPY_REDIRECT_URI"] = spotify_uri
            st.session_state["GOOGLE_API_KEY"] = google_key
            st.rerun()
        else:
            st.error("Bitte fülle alle Felder aus!")
    st.stop()

# Schlüssel in os.environ schreiben, damit andere Module (spfy.py, ai_optimizer.py) darauf zugreifen können
for key in required_keys:
    if key in st.session_state:
        os.environ[key] = st.session_state[key]

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
    st.markdown(f"[Klick hier um dich zu verbinden und füge die Redirect-URL oben ein]({auth_url})")
    st.session_state["auth_manager"] = auth_manager

elif st.button("Optimieren"):
    auth_manager = st.session_state.get("auth_manager")
    if auth_manager and response_url:
        try:
            code = auth_manager.parse_response_code(response_url)
            auth_manager.get_access_token(code)
        except Exception as e:
            st.error(f"Fehler bei der Authentifizierung: {e}")
            st.stop()
    elif not auth_manager:
        st.error("Bitte zuerst auf 'Spotify verbinden' klicken und die Redirect-URL einfügen.")
        st.stop()

    #Prompt Generierung und AI-Optimierung
    with st.spinner("Optimizing your playlist", show_time=False):
        try:
            tracks = spotify_pull_data(playlist_id, auth_manager=auth_manager)
            opt_prompt = generate_prompt(tracks, anzahl_neuer_songs, grenze_gelöschter_songs, playlist_vibe)
            data = playlist_opt(opt_prompt)
            #Speichern der Daten innerhalb der Session
            st.session_state["data"] = data
            #print(data)

        except ServerError as sverror:
            print("Die server sind derzeit überlastet")
            st.markdown("Die server sind derzeit überlastet, versuche es zu einem späteren Zeitpunkt erneut")
        
        except Exception as e:
            st.markdown(f"Es gab einen Fehler: {e}")
        
    
if "data" in st.session_state:
    #Darstellung
    data = st.session_state.get("data")
    if grenze_gelöschter_songs > 0:
        st.subheader("Entfernte Songs")
        st.dataframe(data["removed_songs"])
    if anzahl_neuer_songs > 0:
        st.subheader("Hinzugefügte Songs")
        st.dataframe(data["added_songs"])

    st.subheader("Deine neue Playlist")
    st.dataframe(data["final_playlist"])

    #Playlist bei Spotify hochladen
    playlist_name = st.text_input("Der Name deiner neuen Playlist")

    if st.button("Playlist bei Spotify hochladen"):
        with st.spinner("Uploading your playlist", show_time=False):
            auth_manager = st.session_state.get("auth_manager")
            if auth_manager:
                spotify_push_data(data, playlist_name, auth_manager)
                st.success("Playlist erfolgreich hochgeladen!")
            else:
                st.error("Nicht authentifiziert. Bitte zuerst mit Spotify verbinden.")

