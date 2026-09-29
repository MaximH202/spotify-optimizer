from spfy import spotify_pull_data, spotify_push_data_new_playlist, auth_management, update_playlist, build_final_playlist, parse_playlist_id
from prompt_gen import generate_prompt
from ai_optimizer import playlist_opt
from database import init_db, save_optimization, get_all_optimizations
import streamlit as st
from google.genai.errors import ServerError
from spotipy.cache_handler import CacheHandler
from datetime import timezone
import os
from dotenv import load_dotenv


load_dotenv()

# Datenbank nur einmal pro Serverprozess initialisieren, nicht bei jedem Rerun
@st.cache_resource
def _init_db_once():
    init_db()
    return True

try:
    _init_db_once()
except Exception as e:
    st.error(f"Datenbank nicht erreichbar: {e}")
    st.stop()

# Spotify-Token pro Browser-Session speichern statt in einer gemeinsamen .cache-Datei
class SessionCacheHandler(CacheHandler):
    def get_cached_token(self):
        return st.session_state.get("spotify_token")

    def save_token_to_cache(self, token_info):
        st.session_state["spotify_token"] = token_info

# Liste der benötigten Umgebungsvariablen
required_keys = ["SPOTIPY_CLIENT_ID", "SPOTIPY_CLIENT_SECRET", "SPOTIPY_REDIRECT_URI", "GEMINI_API_KEY"]

# Wert aus st.session_state (Setup-Maske) oder .env holen
def get_key(key):
    return st.session_state.get(key) or os.getenv(key)

# Überprüfen, ob Daten bereits vorhanden sind (in .env oder st.session_state)
def get_missing_keys():
    return [key for key in required_keys if not get_key(key)]

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
        try:
            history = get_all_optimizations()
        except Exception as e:
            history = []
            st.error(f"Verlauf konnte nicht geladen werden: {e}")
        if not history:
            st.toast("Keine Optimierungen gefunden")
        else:
            for entry in history:
                #Formatierung des Datums (gespeichert in UTC, angezeigt in lokaler Zeit)
                if entry.timestamp:
                    date = entry.timestamp.replace(tzinfo=timezone.utc).astimezone().strftime('%d.%m.%Y %H:%M')
                else:
                    date = "Unbekannt"
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
            # Token gehört zu den alten Zugangsdaten
            st.session_state.pop("spotify_token", None)
            st.success("Einstellungen gespeichert!")
            st.rerun()
        else:
            st.error("Bitte fülle alle Felder aus!")

    if not missing_keys:
        if st.button("Abbrechen"):
            st.session_state["show_setup"] = False
            st.rerun()
    st.stop()

st.title("Spotify Playlist Optimizer")

# Spotify Auth initialisieren und Token prüfen
auth_manager = auth_management(
    get_key("SPOTIPY_CLIENT_ID"),
    get_key("SPOTIPY_CLIENT_SECRET"),
    get_key("SPOTIPY_REDIRECT_URI"),
    cache_handler=SessionCacheHandler(),
)
token_info = None
try:
    token_info = auth_manager.validate_token(auth_manager.cache_handler.get_cached_token())
except Exception:
    pass

if not token_info:
    st.info("🔑 Spotify-Verbindung erforderlich")
    auth_url = auth_manager.get_authorize_url()
    st.markdown(f"1. [Klick hier, um dich mit Spotify zu verbinden]({auth_url})\n2. Füge die URL, auf die du weitergeleitet wirst, unten ein.")
    response_url = st.text_input("Redirect-URL einfügen")

    if response_url:
        try:
            code = auth_manager.parse_response_code(response_url)
            auth_manager.get_access_token(code, check_cache=False)
            st.success("Erfolgreich mit Spotify verbunden!")
            st.rerun()
        except Exception as e:
            st.error(f"Fehler bei der Authentifizierung: {e}")
    st.stop()
else:
    st.success("✅ Erfolgreich mit Spotify verbunden.")
    if st.button("Verbindung trennen"):
        # Token und Ergebnisse dieser Session löschen
        st.session_state.pop("spotify_token", None)
        st.session_state.pop("result", None)
        st.rerun()

# Eingabefelder
playlist_input = st.text_input("Playlist-Link oder ID", placeholder="https://open.spotify.com/playlist/...") #Test Playlist: "6TEtUXHUQkQAs2whkLzzlY"
playlist_id = parse_playlist_id(playlist_input)
playlist_vibe = st.text_input("Playlist Vibe | Optional")
anzahl_neuer_songs = st.number_input("Anzahl neuer Songs", min_value=1, max_value=20)
grenze_geloeschter_songs = st.number_input("Anzahl gelöschter Songs", min_value=0, max_value=20)


#Optimierung durchführen
if st.button("Optimieren"):
    #Überprüfen der Eingabefelder
    if not playlist_input.strip():
        st.error("Bitte gib einen Playlist-Link oder eine Playlist ID ein.")
        st.stop()
    if not playlist_id:
        st.error("Ungültiger Playlist-Link. Erwartet z.B. https://open.spotify.com/playlist/... oder eine 22-stellige ID.")
        st.stop()

    # Altes Ergebnis verwerfen, damit bei Fehlern nichts Veraltetes angezeigt/gepusht wird
    st.session_state.pop("result", None)

    #Prompt Generierung und AI-Optimierung
    with st.spinner("Optimizing your playlist", show_time=False):
        try:
            #Spotifydaten holen und AI Optimierung durchführen
            tracks, skipped = spotify_pull_data(playlist_id, auth_manager=auth_manager)
            if not tracks:
                raise ValueError("Die Playlist enthält keine Songs, die optimiert werden können.")
            if skipped:
                st.warning(f"{skipped} Einträge (z.B. lokale Dateien) konnten nicht gelesen werden und sind im Ergebnis nicht enthalten.")

            prompt_tracks = [{k: t[k] for k in ("idx", "artist", "track_name")} for t in tracks]
            opt_prompt = generate_prompt(prompt_tracks, anzahl_neuer_songs, grenze_geloeschter_songs, playlist_vibe)
            ai_data = playlist_opt(opt_prompt, get_key("GEMINI_API_KEY"))

            # Finale Playlist im Code berechnen (bestehende Songs behalten ihre originale URI)
            result = build_final_playlist(tracks, ai_data, grenze_geloeschter_songs, anzahl_neuer_songs, auth_manager)
            result["playlist_id"] = playlist_id

            #Speichern der Daten innerhalb der Session
            st.session_state["result"] = result
        except ServerError:
            st.error("Die Server sind derzeit überlastet, versuche es zu einem späteren Zeitpunkt erneut.")
        except Exception as e:
            st.error(f"Es gab einen Fehler: {e}")

    #Speichern der Daten in der Datenbank (Fehler hier verwerfen das Ergebnis nicht)
    if "result" in st.session_state:
        try:
            save_optimization(playlist_id, playlist_vibe, st.session_state["result"])
        except Exception as e:
            st.warning(f"Ergebnis konnte nicht im Verlauf gespeichert werden: {e}")

#Darstellung und Push der neuen Playlist
if "result" in st.session_state:
    result = st.session_state["result"]
    result_playlist_id = result["playlist_id"]
    final_uris = [t["uri"] for t in result["final_playlist"]]

    def show(songs):
        st.dataframe([{"artist": s["artist"], "track_name": s["track_name"]} for s in songs])

    st.info(f"Optimierung abgeschlossen für Playlist `{result_playlist_id}`. "
            f"Hinzugefügte Songs: {len(result['added_songs'])}. Gelöschte Songs: {len(result['removed_songs'])}")
    if result.get("not_found"):
        st.warning("Diese vorgeschlagenen Songs wurden bei Spotify nicht gefunden und nicht hinzugefügt: "
                   + ", ".join(f"{s.get('track_name')} von {s.get('artist')}" for s in result["not_found"]))
    if playlist_id and playlist_id != result_playlist_id:
        st.warning("Die Playlist ID oben wurde geändert. Das Ergebnis unten gehört weiterhin zur ursprünglichen Playlist.")

    #Entfernte Songs
    if result["removed_songs"]:
        with st.expander("Entfernte Songs"):
            show(result["removed_songs"])
    #Hinzugefügte Songs
    if result["added_songs"]:
        with st.expander("Hinzugefügte Songs"):
            show(result["added_songs"])
    #Final Playlist
    with st.expander("Deine neue Playlist"):
        show(result["final_playlist"])

    # Playlist bei Spotify hochladen
    st.divider()
    with st.expander("🆕 Als neue Playlist speichern", expanded=False):
        playlist_name = st.text_input("Name der neuen Playlist", value="Optimierte Playlist")
        if st.button("Neue Playlist erstellen"):
            if playlist_name:
                with st.spinner("Erstelle neue Playlist...", show_time=False):
                    try:
                        spotify_push_data_new_playlist(final_uris, playlist_name, auth_manager)
                        st.success(f"Playlist '{playlist_name}' erfolgreich erstellt!")
                    except Exception as e:
                        st.error(f"Fehler beim Erstellen: {e}")
            else:
                st.warning("Bitte gib einen Namen für die Playlist ein.")

    # Update der bestehenden Playlist (immer die Playlist, die optimiert wurde)
    st.write(f"Möchtest du die bestehende Playlist `{result_playlist_id}` direkt aktualisieren?")
    if st.button("🔄 Bestehende Playlist aktualisieren"):
        with st.spinner("Aktualisiere Playlist...", show_time=False):
            try:
                update_playlist(result_playlist_id, final_uris, auth_manager)
                st.success("Playlist erfolgreich aktualisiert!")
            except Exception as e:
                st.error(f"Fehler beim Update: {e}")
