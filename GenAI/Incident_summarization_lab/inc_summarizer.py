import streamlit as st
import pandas as pd
import os
##from langchain_openai import AzureChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
##from langchain.prompts import ChatPromptTemplate
from langchain_core.prompts import ChatPromptTemplate
#from langchain.chains import LLMChain
#from langchain.chains.llm import LLMChain

from dotenv import load_dotenv
from Step0 import run_preprocessing
#from Step2 import run_step2

# Set environment variables LLM KeyError

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0.7  # Set your desired temperature here
)


# Define the prompt template
prompt_template = ChatPromptTemplate.from_template(
    """
    You are an expert IT support assistant and working on the job of building a knowledge base and creating necessary templates for usage. 
    Based on the following incident ticket details:
    
    - Issue Description: {Issue_Description}
    - Category: {Category}
    - Sub-Category: {Subcategory}
    - Resolution_Notes: {Resolution_Notes}
    
    Please do the following:
    
    1. Use the combination of all 4 columns to understand the issue well and rephrase the 'Resolution_Notes' in a very professional way.
    2. Capture the life-cycle of the incident in short and professional language.
    3. Re-write the steps as instructions.
    4. If there are multiple scenarios involved, split and construct the summary accordingly 
    
    Format your response in the format of a knowledge article:
    
    Category:{Category} | Sub-Category: {Subcategory}
    ---
    Resolution Steps:
    [bullet points]
    ---
    """
)


# Create the LLM chain
chain = prompt_template | llm


st.title("AI Bees - Operational Assistant")



tab1, tab2 = st.tabs(["Step 0: Incident Preprocessor","Step 1: Incident Summarization"])

with tab1:

    run_preprocessing()
    
    
with tab2:
    st.header("Incident Summarization")
    # Input for number of rows to process
    param = st.number_input("Enter number of rows to process:", min_value=1, value=20, step=1)

    # Start button
    if st.button("▶ Compose Incident Summary"):
    ##if st.button("Start Processing"):
        try:
            df2 = pd.read_csv('inc_data_final.csv', encoding="latin1")
            df2 = df2.dropna(subset=['Subcategory', 'Assignment_group', 'Resolution_Notes'])
            df = df2.head(param)
            
            def generate_notes(row):
                inputs = {
                    "Issue_Description": row["Issue_Description"],
                    "Category": row["Category"],
                    "Subcategory": row["Subcategory"],
                    "Resolution_Notes": row["Resolution_Notes"]
                }
                response = chain.invoke(inputs)
                return response.content

            df["Incident_Summary"] = df.apply(generate_notes, axis=1)
            # Save the output to a CSV file
            output_file = "step1_output.csv"
            header = ["Issue_Description", "Category", "Subcategory", "Assignment_group", "Resolution_Notes", "Incident_Summary"]
            df.to_csv(output_file, index=False, columns=header)

            # Display the top 5 rows
            st.success(f"✅   Incident Summarization is completed.. {output_file}")
            st.dataframe(df)

        except Exception as e:
            st.error(f"An error occurred: {e}")

