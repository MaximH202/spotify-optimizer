from google import genai
from google.genai import types
import json
import re

#Initialisierung von Gemini und Spotify Playlist Optimierung
def playlist_opt(prompt: str, api_key: str):
    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    if not response.text:
        raise ValueError("Die KI hat keine Antwort geliefert (evtl. blockiert). Bitte erneut versuchen.")

    # Falls trotzdem Markdown-Codeblöcke kommen, diese entfernen
    clean = re.sub(r"^```[a-zA-Z]*\s*|\s*```$", "", response.text.strip())
    try:
        data = json.loads(clean)
    except json.JSONDecodeError as e:
        raise ValueError(f"Die KI-Antwort ist kein gültiges JSON: {e}") from e

    if not isinstance(data, dict):
        raise ValueError("Die KI-Antwort hat ein unerwartetes Format.")
    for key in ("removed_songs", "added_songs"):
        value = data.get(key, [])
        if not isinstance(value, list):
            raise ValueError(f"'{key}' in der KI-Antwort ist keine Liste.")
        data[key] = [s for s in value if isinstance(s, dict)]
    return data
