import streamlit as st
import google.generativeai as genai
import os
import PyPDF2 as pdf
from dotenv import load_dotenv
import json
import re

load_dotenv ()  # Load environment variables

# Configure the Google Generative AI API
genai.configure ( api_key=os.getenv ( "GOOGLE_API_KEY" ) )


def get_gemini_response(input_prompt):
    """Get response from Gemini API using the input prompt."""
    model=genai.GenerativeModel ( 'gemini-pro' )
    response=model.generate_content ( input_prompt )
    return response.text.strip ()  # Clean the response


def extract_pdf_text(uploaded_file):
    """Extract text from the uploaded PDF file."""
    reader=pdf.PdfReader ( uploaded_file )
    text=""
    for page in range ( len ( reader.pages ) ):
        page=reader.pages[page]
        text+=str ( page.extract_text () )
    return text


# Prompt Template for the ATS
prompt_template="""
Hey, act as a skilled ATS (Applicant Tracking System) with expertise in analyzing resumes and job descriptions.
Evaluate the resume provided based on the job description. 
Your output should include:
1. Job Description Match percentage (0% to 100%),
2. Missing Keywords that are important for the job,
3. A concise Profile Summary highlighting the candidate's strengths.

Resume: {resume}
Job Description: {jd}

Your response must follow this exact JSON format:
{{
    "Job Description Match": "<percentage>%",
    "Missing Keywords": ["<keyword1>", "<keyword2>", ...],
    "Profile Summary": "<summary>"
}}
"""

# Streamlit Application
st.title ( "Smart ATS - Job Matching Assistant" )
st.text ( "Upload your resume and provide the job description for analysis." )

# Input fields
job_description=st.text_area ( "Paste the Job Description", help="Enter the job description for the position." )
uploaded_file=st.file_uploader ( "Upload Your Resume", type="pdf", help="Upload your resume as a PDF file." )
submit=st.button ( "Submit" )

if submit:
    if uploaded_file is not None and job_description.strip ():
        resume_text=extract_pdf_text ( uploaded_file )
        # Prepare the prompt
        input_prompt=prompt_template.format ( resume=resume_text, jd=job_description )
        # Get response from Gemini API
        try:
            response=get_gemini_response ( input_prompt )

            # Clean the response to remove markdown and ensure valid JSON
            response_cleaned=re.sub ( r'```json\s*|\s*```', '',
                                      response ).strip ()  # Remove the markdown and extra spaces

            # Ensure the response is valid JSON
            try:
                parsed_response=json.loads ( response_cleaned )
                st.subheader ( "ATS Analysis Result" )
                st.json ( parsed_response )  # Display the clean JSON response
            except json.JSONDecodeError:
                st.error ( "Error: The response from Gemini is not valid JSON. Please try again." )
                st.error ( f"Raw response: {response_cleaned}" )
        except Exception as e:
            st.error ( "Error occurred while processing. Please try again." )
            st.error ( f"Details: {e}" )
    else:
        st.warning ( "Please upload a resume and provide a job description!" )