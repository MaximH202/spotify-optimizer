from google import genai
from dotenv import load_dotenv
import json

def playlist_opt(prompt : str):
    load_dotenv()
    client = genai.Client()

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=f"{prompt}",
    )

    clean = response.text.strip().removeprefix("```json").removesuffix("``").strip()
    data = json.loads(clean)

    return data
