import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

# Initialize the model
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key = os.getenv("GOOGLE_API_KEY"),
    temperature=0.7) # 0 - 2  

print("--- Welcome to the Personalized Chatbot (type 'exit' or 'quit' to end) --- ")

while True:
    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit"]:
        print("Goodbye!")
        break
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": user_input}
    ]
    response = llm.invoke(messages)
    print(f"Bot: {response.content}")