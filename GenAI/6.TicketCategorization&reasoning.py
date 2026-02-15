"""
Usecase:
Automated Customer Support Ticket Categorization & Priority Routing.

Description:
This example demonstrates how to use Few-Shot prompting combined with 
Chain-of-Thought (CoT) reasoning to categorize and prioritize customer support tickets. 
The model is provided with examples of how to analyze tickets, identify key factors 
(like urgency, tone, and issue type), and then apply that reasoning to a new ticket. 
This approach helps ensure consistent and accurate categorization and routing of support requests.
"""
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0.2, # Lower temperature for consistent categorization logic
)

# 1. Few-Shot Examples
examples_str = """
Example 1:
Ticket: "My password isn't working and I have a huge presentation in 10 minutes! Please help!"
Reasoning: 
1. The user is locked out (Access Issue).
2. The tone is high-stress ("huge presentation").
3. The timeframe is immediate (10 minutes).
Category: Account Access
Priority: CRITICAL

Example 2:
Ticket: "I noticed a small typo on the 'About Us' page. It's not urgent, just thought you'd like to know."
Reasoning:
1. This is a visual/content error (UI/UX).
2. The tone is calm and helpful.
3. The user explicitly stated it is not urgent.
Category: Website Content
Priority: LOW

Provide priority levels as CRITICAL and LOW only.
"""

# 2. The Current Ticket (The "Task")
current_ticket = "The checkout button is disappearing when I try to pay with a Credit Card. I've tried three times and I'm worried I'll be double charged."

# 3. Combine both Few-Shot and CoT in the messages
messages = [
    {
        "role": "system", 
        "content": f"""You are a Support Triage Bot. 
Follow the reasoning style and categorization format in the examples below:
---
{examples_str}
---"""
    },
    {
        "role": "user", 
        "content": f"Analyze this ticket and provide the Reasoning, Category, and Priority:\nTicket: {current_ticket}"
    }
]

result = llm.invoke(messages).content
print(result)