from spfy import spotify_pull_data, spotify_push_data_new_playlist, auth_management, update_playlist
from prompt_gen import generate_prompt
from ai_optimizer import playlist_opt
import json
from database import init_db, save_optimization, get_all_optimizations
import streamlit as st
from google.genai.errors import ServerError
import os
from dotenv import load_dotenv


load_dotenv()
init_db()

# Liste der benötigten Umgebungsvariablen
required_keys = ["SPOTIPY_CLIENT_ID", "SPOTIPY_CLIENT_SECRET", "SPOTIPY_REDIRECT_URI", "GEMINI_API_KEY"]

# Überprüfen, ob Daten bereits vorhanden sind (in .env oder st.session_state)
def get_missing_keys():
    return [key for key in required_keys if not os.getenv(key) and key not in st.session_state]

if "show_setup" not in st.session_state:
    st.session_state["show_setup"] = False

# Sidebar für Reset und Verlauf
with st.sidebar:
    st.title("⚙️ Einstellungen")
    if st.button("API-Keys zurücksetzen"):
        for key in required_keys:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state["show_setup"] = True
        st.rerun()

    if st.button("Verlauf anzeigen"):
        history = get_all_optimizations()
        if not history:
            st.toast("Keine Optimierungen gefunden")
        else:
            for entry in reversed(history):
                #Formatierung des Datums
                date = entry.timestamp.strftime('%d.%m.%Y %H:%M') if entry.timestamp else "Unbekannt"
                with st.expander(f"📅 {date} | Vibe: {entry.vibe or 'Keiner'}"):
                    st.write(f"**Playlist ID:** `{entry.playlist_id}`")
                    # anzeigen der Ergebnisse als JSON
                    st.json(entry.results)

missing_keys = get_missing_keys()

# Falls Daten fehlen -> Setup anzeigen
if missing_keys or st.session_state["show_setup"]:
    st.title("⚙️ Setup")
    st.info("Bitte gib deine API-Daten ein. Sobald du speicherst, verschwindet dieses Menü.")
    
    spotify_id = st.text_input("Spotify Client ID", value=st.session_state.get("SPOTIPY_CLIENT_ID", ""))
    spotify_secret = st.text_input("Spotify Client Secret", type="password", value=st.session_state.get("SPOTIPY_CLIENT_SECRET", ""))
    spotify_uri = st.text_input("Spotify Redirect URI", value=st.session_state.get("SPOTIPY_REDIRECT_URI", ""))
    gemini_key = st.text_input("Gemini API Key", type="password", value=st.session_state.get("GEMINI_API_KEY", ""))
    
    if st.button("Einstellungen speichern"):
        if spotify_id and spotify_secret and spotify_uri and gemini_key:
            st.session_state["SPOTIPY_CLIENT_ID"] = spotify_id
            st.session_state["SPOTIPY_CLIENT_SECRET"] = spotify_secret
            st.session_state["SPOTIPY_REDIRECT_URI"] = spotify_uri
            st.session_state["GEMINI_API_KEY"] = gemini_key
            st.session_state["show_setup"] = False
            st.success("Einstellungen gespeichert!")
            st.rerun()
        else:
            st.error("Bitte fülle alle Felder aus!")
    
    if not missing_keys:
        if st.button("Abbrechen"):
            st.session_state["show_setup"] = False
            st.rerun()
    st.stop()

# Schlüssel in os.environ schreiben, damit andere Module (spfy.py, ai_optimizer.py) darauf zugreifen können
for key in required_keys:
    if key in st.session_state:
        os.environ[key] = st.session_state[key]

st.title("Spotify Playlist Optimizer")

# Spotify Auth initialisieren und Token prüfen
auth_manager = auth_management()
token_info = None
try:
    token_info = auth_manager.get_cached_token()
except Exception:
    pass

#Überprüfen, ob Spotify verbunden ist
is_authenticated = False
if token_info:
    st.session_state["auth_manager"] = auth_manager
    is_authenticated = True

if not is_authenticated:
    st.info("🔑 Spotify-Verbindung erforderlich")
    response_url = st.text_input("Redirect-URL einfügen")
    
    if st.button("Spotify verbinden"):
        auth_url = auth_manager.get_authorize_url()
        st.markdown(f"[Klick hier um dich zu verbinden und füge die Redirect-URL oben ein]({auth_url})")
        st.session_state["auth_manager"] = auth_manager
    
    if response_url:
        try:
            code = auth_manager.parse_response_code(response_url)
            auth_manager.get_access_token(code)
            st.success("Erfolgreich mit Spotify verbunden!")
            st.rerun()
        except Exception as e:
            st.error(f"Fehler bei der Authentifizierung: {e}")
            st.stop()
    st.stop()
else:
    st.success("✅ Erfolgreich mit Spotify verbunden.")
    if st.button("Verbindung trennen"):
        # Cache löschen und session_state zurücksetzen
        if os.path.exists(".cache"):
            os.remove(".cache")
        if "auth_manager" in st.session_state:
            del st.session_state["auth_manager"]
        st.rerun()

# Eingabefelder
playlist_id = st.text_input("Playlist ID") #Test Playlist: "6TEtUXHUQkQAs2whkLzzlY"
playlist_vibe = st.text_input("Playlist Vibe | Optional")
anzahl_neuer_songs = st.number_input("Anzahl neuer Songs", min_value=1, max_value=20)
grenze_geloeschter_songs = st.number_input("Anzahl gelöschter Songs", min_value=0, max_value=20)

#Session State für Daten
if 'key' not in st.session_state:
    st.session_state.key = 'value'


#Optimierung durchführen und Spotify API mit Push-Funktionalität
if st.button("Optimieren"):
    auth_manager = st.session_state.get("auth_manager")
    
    #Überprüfen der Eingabefelder    
    if not auth_manager:
        st.error("Bitte zuerst mit Spotify verbinden.")
        st.stop()
    elif not playlist_id:
        st.error("Bitte gib eine Playlist ID ein.")
        st.stop()
    elif not anzahl_neuer_songs:
        st.error("Bitte gib die Anzahl neuer Songs ein.")
        st.stop()
    elif not grenze_geloeschter_songs:
        st.error("Bitte gib die Anzahl gelöschter Songs ein.")
        st.stop()

    #Prompt Generierung und AI-Optimierung
    with st.spinner("Optimizing your playlist", show_time=False):
        try:
            #Spotifydaten holen und AI Optimierung durchführen
            tracks = spotify_pull_data(playlist_id, auth_manager=auth_manager)
            opt_prompt = generate_prompt(tracks, anzahl_neuer_songs, grenze_geloeschter_songs, playlist_vibe)
            data = playlist_opt(opt_prompt)
            
            #Speichern der Daten innerhalb der Session
            st.session_state["data"] = data
            #Speichern der Daten in der Datenbank
            save_optimization(playlist_id, playlist_vibe, data)
        except ServerError as sverror:
            print("Die server sind derzeit überlastet")
            st.markdown("Die server sind derzeit überlastet, versuche es zu einem späteren Zeitpunkt erneut")
        
        except Exception as e:
            st.error(f"Es gab einen Fehler: {e}")
        
#Darstellung und Push der neuen Playlist
if "data" in st.session_state:
    #Darstellung der Ergebnisse
    data = st.session_state.get("data")
    num_added = len(data.get("added_songs", []))
    num_removed = len(data.get("removed_songs", []))
    st.info(f"Optimierung abgeschlossen. Hinzugefügte Songs: {num_added}. Gelöschte Songs: {num_removed}")

    #Entfernte Songs
    if grenze_geloeschter_songs > 0:
        with st.expander("Entfernte Songs"):
            st.dataframe(data["removed_songs"])
    #Hinzugefügte Songs
    if anzahl_neuer_songs > 0:
        with st.expander("Hinzugefügte Songs"):
            st.dataframe(data["added_songs"])
    #Final Playlist
    with st.expander("Deine neue Playlist"):
        st.dataframe(data["final_playlist"])

    # Playlist bei Spotify hochladen
    st.divider()
    with st.expander("🆕 Als neue Playlist speichern", expanded=False):
        playlist_name = st.text_input("Name der neuen Playlist", value="Optimierte Playlist")
        if st.button("Neue Playlist erstellen"):
            if playlist_name:
                with st.spinner("Erstelle neue Playlist...", show_time=False):
                    auth_manager = st.session_state.get("auth_manager")
                    if auth_manager:
                        spotify_push_data_new_playlist(data, playlist_name, auth_manager)
                        st.success(f"Playlist '{playlist_name}' erfolgreich erstellt!")
                    else:
                        st.error("Nicht authentifiziert. Bitte zuerst mit Spotify verbinden.")
            else:
                st.warning("Bitte gib einen Namen für die Playlist ein.")
    
    # Update der bestehenden Playlist
    st.write("Möchtest du die bestehende Playlist direkt aktualisieren?")
    if st.button("🔄 Bestehende Playlist aktualisieren"):
        if playlist_id:
            with st.spinner("Aktualisiere Playlist...", show_time=False):
                auth_manager = st.session_state.get("auth_manager")
                try:
                    update_playlist(playlist_id, data, auth_manager)
                    st.success("Playlist erfolgreich aktualisiert!")
                except Exception as e:
                    st.error(f"Fehler beim Update: {e}")
        else:
            st.error("Keine Playlist ID gefunden. Bitte oben eingeben.")


