import os
from dotenv import load_dotenv
from google import genai

load_dotenv()  # reads .env into environment variables
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

resp = client.models.generate_content(
    model="gemini-3.5-flash-lite",
    contents="Reply with exactly: AskData is alive",
)
print(resp.text)
print("Tokens used:", resp.usage_metadata.total_token_count)
