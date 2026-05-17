# 🎵 Spotify Playlist Optimizer

Der **Spotify Playlist Optimizer** ist eine moderne, interaktive Webanwendung, die mithilfe von künstlicher Intelligenz (Google Gemini) deine Spotify-Playlists analysiert, bereinigt und passend zu einer gewünschten Stimmung (Vibe) mit neuen Lizenztiteln erweitert. 

Die Ergebnisse werden übersichtlich dargestellt, können in einer lokalen Datenbank (PostgreSQL/SQLite) historisiert werden und lassen sich direkt wieder auf Spotify exportieren – entweder als neue Playlist oder durch direkte Aktualisierung der bestehenden Playlist.

---

## Features

- **🔑 Spotify-Authentifizierung:** Login per Redirect-URL
- **🧠 KI (Google Gemini 3 / Gemini Flash):** Intelligente Optimierung deiner Playlist auf Basis von Genre, BPM und Stimmung. Die KI entfernt unpassende Songs (ohne die musikalische DNA der Playlist zu zerstören) und fügt passende, real existierende Titel hinzu.
- **⚙️ Flexible Kriterien:** Bestimme selbst den Ziel-Vibe (oder lass ihn automatisch ermitteln), die Anzahl neuer Songs und das Limit für gelöschte Songs.
- **📊 Interaktive UI:** Oberfläche mit Streamlit, Vorher-Nachher-Tabellen (Entfernte Songs, Hinzugefügte Songs, Finale Playlist) und ausklappbaren Elementen.
- **🔄 Spotify-Synchronisierung:** 
  - Speichere die optimierte Liste als **neue Playlist** auf deinem Spotify-Konto ab.
  - Überschreibe und aktualisiere die **bestehende Playlist** direkt auf Spotify.
- **📅 Verlauf:** Jede Optimierung wird automatisch in einer Datenbank gespeichert. In der Sidebar kannst du den Verlauf aller vergangenen Optimierungen inklusive Datum, Vibe und Ergebnissen einsehen.
- **🐳 Dockerized:** Vollständiges Container-Setup mit Docker Compose, inklusive automatischer Datenbank-Initialisierung.

---

## 🛠️ Technologien

- **Frontend & UI:** [Streamlit](https://streamlit.io/)
- **Spotify-API-Anbindung:** [Spotipy](https://spotipy.readthedocs.io/)
- **KI-Modell:** [Google Gemini API](https://ai.google.dev/) via modernes `google-genai` SDK (`gemini-3-flash-preview`)
- **Datenbank & ORM:** PostgreSQL (Docker) / SQLite (Lokaler Fallback) via [SQLAlchemy](https://www.sqlalchemy.org/)
- **Containerisierung:** [Docker](https://www.docker.com/) & Docker Compose

---

## 🚀 Setup & Installation

### 1. API-Keys besorgen

#### **Spotify API:**
1. Gehe zum [Spotify for Developers Dashboard](https://developer.spotify.com/dashboard).
2. Erstelle eine neue App.
3. Gib als **Redirect URI** beispielsweise `http://localhost:8501/` oder `http://localhost:8080/` in den App-Einstellungen an.
4. Kopiere die `Client ID`, das `Client Secret` und die `Redirect URI`.

#### **Gemini API:**
1. Gehe zum [Google AI Studio](https://aistudio.google.com/api-keys).
2. Erstelle einen neuen API-Key und kopiere ihn.

---

### 2. Konfiguration (`.env`)

Erstelle eine `.env`-Datei im Hauptverzeichnis des Projekts und füge deine Zugangsdaten ein:

```env
SPOTIPY_CLIENT_ID=deine_client_id
SPOTIPY_CLIENT_SECRET=dein_client_secret
SPOTIPY_REDIRECT_URI=deine_redirect_uri
GEMINI_API_KEY=dein_gemini_api_key
```

*Hinweis: Wenn diese Variablen in der `.env`-Datei gesetzt sind, lädt die App sie automatisch. Alternativ können sie beim ersten Start auch direkt in der Setup-Oberfläche der App eingegeben und im Session-State gespeichert werden.*

---

### 3. Starten der Anwendung

Du hast zwei Möglichkeiten, die Anwendung auszuführen:

#### **Option A: Mit Docker & Docker Compose (Empfohlen)**
Diese Option startet die Streamlit-App sowie eine vollkonfigurierte PostgreSQL-Datenbank im Hintergrund.

1. Stelle sicher, dass Docker installiert ist und läuft.
2. Führe im Hauptverzeichnis aus:
   ```bash
   docker compose up --build
   ```
3. Öffne im Browser: [http://localhost:8501](http://localhost:8501)

#### **Option B: Lokal (Ohne Docker)**
1. Erstelle eine virtuelle Umgebung und installiere die Abhängigkeiten:
   ```bash
   python -m venv venv

   venv\Scripts\activate

   pip install -r requirements.txt
   ```
2. Starte die Streamlit-App:
   ```bash
   streamlit run src/app.py
   ```
3. Öffne im Browser: [http://localhost:8501](http://localhost:8501)

---

## 📁 Projektstruktur

```text
Spotify-Optimizer/
├── .devcontainer/        # Entwicklungsumgebung für VS Code
├── src/
│   ├── app.py            # Streamlit UI & Hauptanwendung
│   ├── spfy.py           # Spotify API-Schnittstellen (Spotipy)
│   ├── ai_optimizer.py   # Gemini API-Anbindung (Generierung)
│   ├── prompt_gen.py     # Prompt-Template-Generierung
│   └── database.py       # SQLAlchemy DB-Modelle & -Funktionen
├── dockerfile            # Docker-Konfiguration für die App
├── docker-compose.yml    # Docker Compose-Konfiguration (App + PostgreSQL)
├── requirements.txt      # Python-Abhängigkeiten
├── .gitignore            # Git-Ausschlussregeln (ignoriert .env, .cache etc.)
└── README.md             # Diese Dokumentation
```

---

## 🛡️ Sicherheitshinweis

- Teile niemals deine `.env`-Datei oder die `.cache`-Dateien
- Beide Dateien sind bereits in der `.gitignore` eingetragen und werden nicht in dein Git-Repository übertragen.
