## ⚙️ Setup

### 1. Umgebungsvariablen
Erstelle eine `.env` Datei im Root-Verzeichnis des Projekts mit folgenden Variablen:

SPOTIPY_CLIENT_ID=deine_client_id
SPOTIPY_CLIENT_SECRET=dein_client_secret
SPOTIPY_REDIRECT_URI=dein_redirect_URI
GEMINI_API_KEY=dein_api_key

### 2. API Keys erhalten

**Spotify:**
1. Gehe zu [Spotify for Developers](https://developer.spotify.com/dashboard)
2. Erstelle eine neue App
3. Kopiere `Client ID`, `Client Secret` und `Redirect URIs` (Beispiel für ein Redirect URI ist `https://example.com/callback`)

**Gemini:**
1. Gehe zu [Google AI Studio](https://aistudio.google.com/api-keys)
2. Erstelle einen neuen API Key