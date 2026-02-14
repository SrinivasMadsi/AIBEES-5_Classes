import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

# Initialize the model
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key = os.getenv("GOOGLE_API_KEY"),
    temperature=0.7) # 0 - 2  

# Prepare messages system and user
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Give me a Joke on AI"}
]

# Invoke the model
response = llm.invoke(messages)
print(response.content)