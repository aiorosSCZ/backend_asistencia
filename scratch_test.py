import os
from dotenv import load_dotenv
load_dotenv(override=True)

from google import genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
print("KEY:", GEMINI_API_KEY[:15] + "...")

client = genai.Client(api_key=GEMINI_API_KEY)
response = client.models.generate_content(
    model='gemini-flash-latest',
    contents='Respond with the word: HELLO'
)
print("RESPONSE:", response.text)
