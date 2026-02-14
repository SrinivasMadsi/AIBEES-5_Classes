import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
import streamlit as st
load_dotenv()

llm = ChatGoogleGenerativeAI(
    model = "gemini-2.5-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0.7,  # 0 - 2
    # max_output_tokens=100,
)

st.title("Google Gemini LLM with Streamlit")

question = st.text_input("Enter your question:")

if st.button("Get Answer"):
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},  
        {"role": "user", "content": question}
        ]
    st.write("**Answer:**")
    st.write(llm.invoke(messages).content)

