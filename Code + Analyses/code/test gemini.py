import os
from google import genai

client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

print("=== Beschikbare modellen voor deze key ===")
for m in client.models.list():
    if "gemini" in m.name:
        print(m.name)

print("\n=== Test call ===")
try:
    resp = client.models.generate_content(
        model="gemini-3.1-pro-preview",
        contents="Zeg alleen het woord: OK"
    )
    print("Antwoord:", resp.text)
except Exception as e:
    print(f"FOUT ({type(e).__name__}): {e}")