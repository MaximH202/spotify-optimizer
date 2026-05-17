from google import genai
from dotenv import load_dotenv
import json

#Initialisierung von Gemini und Spotify Playlist Optimierung
def playlist_opt(prompt : str):
    load_dotenv()
    client = genai.Client()

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents= prompt,
    )
    clean = response.text.strip().removeprefix("```json").removesuffix("```").strip()
    return json.loads(clean)
