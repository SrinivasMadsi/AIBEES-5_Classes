# # ## Test the model using python 
# from langchain_ollama import OllamaLLM
  
# ollama = OllamaLLM(base_url='http://localhost:11434', model='llama3.2:1b')
# question = "What is the capital of France?"
# result = ollama.invoke(question)
# print(result)


## Using Python without running the ollama serve

import subprocess
import time
import warnings
from langchain_ollama import OllamaLLM

warnings.filterwarnings("ignore")

OLLAMA_EXE = r"C:\Users\medsi\AppData\Local\Programs\Ollama\ollama.exe" # Path to ollama executable

# Start server silently
server = subprocess.Popen(
    [OLLAMA_EXE, "serve"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)

time.sleep(5)

ollama = OllamaLLM(base_url='http://localhost:11434', model='llama3.2:1b')
result = ollama.invoke("What is the capital of France?")
print(result)

server.terminate()
