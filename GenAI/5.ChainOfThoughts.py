import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key = os.getenv("GOOGLE_API_KEY"),
    temperature=0.7)

message = [
    {
        "role": "system",
        "content": "You are a helpful assistant. Solve the problem step by step and explain your reasoning."
    },
    {
        "role": "user",
        "content": "If john age is 10 years and his sister is half his age, how old is his sister when he is 50?"
    }
]

result = llm.invoke(message).content
print(result)