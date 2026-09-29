import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Spotify erlaubt max. 100 Items pro Add/Replace-Request
CHUNK_SIZE = 100

#Auth_manager initialisieren (Token wird über den cache_handler pro Session gespeichert)
def auth_management(client_id: str, client_secret: str, redirect_uri: str, cache_handler=None):
    auth_manager = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope="playlist-modify-public playlist-modify-private user-library-read",
        open_browser=False,
        cache_handler=cache_handler,
    )
    return auth_manager

#Spotify Datenabruf (alle Seiten der Playlist)
def spotify_pull_data(playlist_id: str, auth_manager):
    sp = spotipy.Spotify(auth_manager=auth_manager)

    tracks = []
    skipped = 0
    results = sp.playlist_items(playlist_id, limit=50)
    while results:
        for item in results.get('items', []):
            # Neues API-Feld "item", älteres Feld "track"
            track = item.get('item') or item.get('track')
            if not track or not track.get('uri') or item.get('is_local') or track.get('is_local'):
                # Lokale Dateien können über die API nicht wieder hinzugefügt werden
                skipped += 1
                continue
            artists = track.get('artists')
            if not artists:
                skipped += 1
                continue
            tracks.append({
                "idx": len(tracks),
                "artist": artists[0]['name'],
                "track_name": track.get('name', 'Unbekannt'),
                "uri": track['uri'],
            })
        results = sp.next(results) if results.get('next') else None
    return tracks, skipped

#URI eines Songs über die Suche ermitteln
def search_uri(sp, track_name: str, artist_name: str):
    if not track_name:
        return None
    # Erst exakte Feldsuche, dann freie Suche mit Titel + Künstler.
    # Keine Suche nur nach Titel, da diese oft einen falschen Song liefert.
    queries = [f"track:{track_name} artist:{artist_name}", f"{track_name} {artist_name}"]
    for q in queries:
        result = sp.search(q, limit=1, type='track')
        items = result.get("tracks", {}).get("items", [])
        if items:
            return items[0]
    return None

def _norm(text):
    return (text or "").strip().casefold()

#Finale Playlist aus Originaldaten + KI-Vorschlägen berechnen
def build_final_playlist(tracks: list, data: dict, max_removed: int, max_added: int, auth_manager):
    sp = spotipy.Spotify(auth_manager=auth_manager)

    # Zu entfernende Songs bestimmen: über idx (wenn Name passt), sonst über Artist + Titel
    removed_idx = []
    for song in data.get("removed_songs", []):
        if len(removed_idx) >= max_removed:
            break
        idx = song.get("idx")
        match = None
        if isinstance(idx, int) and 0 <= idx < len(tracks) and _norm(tracks[idx]["track_name"]) == _norm(song.get("track_name")):
            match = idx
        else:
            for t in tracks:
                if _norm(t["track_name"]) == _norm(song.get("track_name")) and _norm(t["artist"]) == _norm(song.get("artist")):
                    match = t["idx"]
                    break
        if match is not None and match not in removed_idx:
            removed_idx.append(match)

    removed = [tracks[i] for i in removed_idx]
    final = [t for t in tracks if t["idx"] not in removed_idx]
    existing_uris = {t["uri"] for t in final}

    # Neue Songs suchen, Duplikate und nicht gefundene Songs überspringen
    added, not_found = [], []
    for song in data.get("added_songs", []):
        if len(added) >= max_added:
            break
        found = search_uri(sp, song.get("track_name"), song.get("artist"))
        if not found:
            not_found.append(song)
            continue
        if found["uri"] in existing_uris:
            continue
        existing_uris.add(found["uri"])
        new_track = {
            "artist": found["artists"][0]["name"] if found.get("artists") else song.get("artist"),
            "track_name": found.get("name", song.get("track_name")),
            "uri": found["uri"],
        }
        added.append(new_track)
        final.append(new_track)

    return {"removed_songs": removed, "added_songs": added, "final_playlist": final, "not_found": not_found}

def _chunks(items: list):
    for i in range(0, len(items), CHUNK_SIZE):
        yield items[i:i + CHUNK_SIZE]

#Spotify Push Playlist
def spotify_push_data_new_playlist(uris: list, playlist_name: str, auth_manager):
    if not uris:
        raise ValueError("Die finale Playlist ist leer, es wurde nichts erstellt.")
    sp = spotipy.Spotify(auth_manager=auth_manager)

    # Playlist-Name Standardwert falls leer
    if not playlist_name:
        playlist_name = "AI Optimized Playlist"

    playlist = sp.current_user_playlist_create(
        playlist_name,
        public=True,
        collaborative=False,
        description='Your new Playlist, optimized by AI'
    )
    for chunk in _chunks(uris):
        sp.playlist_add_items(playlist["id"], chunk)
    return playlist

#Playlist aktualisieren
def update_playlist(playlist_id: str, uris: list, auth_manager):
    if not uris:
        raise ValueError("Die finale Playlist ist leer, die Playlist wurde nicht verändert.")
    sp = spotipy.Spotify(auth_manager=auth_manager)
    chunks = list(_chunks(uris))
    # Replace setzt die ersten 100 Songs, der Rest wird angehängt
    sp.playlist_replace_items(playlist_id, chunks[0])
    for chunk in chunks[1:]:
        sp.playlist_add_items(playlist_id, chunk)
