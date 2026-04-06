from google import genai
from dotenv import load_dotenv
from prompt import prompt

load_dotenv()
client = genai.Client()

response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=f"{prompt}",
)

print(response.text)