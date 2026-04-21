from google import genai

client = genai.Client(api_key="AIzaSyD3Q8AiB0eZTsKan02atc4h9kRzNfSGQrY")
response = client.models.generate_content(
    model="gemini-flash-lite-latest",
    contents="Hello, say something",
    config={"temperature": 0.1}
)
print(response.text)