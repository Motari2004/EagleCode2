from google import genai

client = genai.Client(api_key="AIzaSyCSsRRaUI3d90DiJQx24kHz7gkSupZURGg")
response = client.models.generate_content(
    model="gemini-flash-lite-latest",
    contents="Hello, say something",
    config={"temperature": 0.1}
)
print(response.text)