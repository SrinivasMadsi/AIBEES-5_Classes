import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key = os.getenv("GOOGLE_API_KEY"),
    temperature=0.7)


# Few-shot prompting for email subject line generation

message = [
    {
        "role": "system",
        "content": "You are a helpful assistant that generates email subject lines based on the email content. If the question is not related to email then you need to return 'Not an email content'."
    },
    {
        "role": "user",
        "content": "Email content: 'I hope this email finds you well. I wanted to follow up on our previous conversation about the project timeline. Please let me know if you have any updates or if we can schedule a meeting to discuss further.'"
    },
    {
        "role": "assistant",
        "content": "Subject line: 'Follow-up on Project Timeline'"
    },
    {
        "role": "user",
        "content": "Email content: 'I am writing to inform you about the upcoming changes to our product line. We will be launching new features next month, and I wanted to give you a heads-up so you can prepare accordingly.'"
    },
    {
        "role": "assistant",
        "content": "Subject line: 'Upcoming Product Line Changes and New Features'"
    },
    {
        "role": "user",
        # change your question here to test the model's ability to recognize non-email content
        "content": "What is Anthropic?"
    }
]

# Invoke the model with the few-shot prompt
result  = llm.invoke(message).content
print(result)
