import streamlit as st
import google.generativeai as genai
import os
import PyPDF2 as pdf
from dotenv import load_dotenv
import json
import re
import matplotlib.pyplot as plt

# Load environment variables
load_dotenv()

# Configure the Google Generative AI API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Define utility functions
def get_gemini_response(input_prompt):
    """Get response from Gemini API using the input prompt."""
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(input_prompt)
    return response.text.strip()

def extract_pdf_text(uploaded_file):
    """Extract text from the uploaded PDF file."""
    reader = pdf.PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

# Updated Prompt Template for ATS (with dynamic feedback generation)
prompt_template = """
Hey, act as a skilled ATS (Applicant Tracking System) with expertise in analyzing resumes and job descriptions.
Evaluate the resume provided based on the job description.
Your output should include:
1. Job Description Match percentage (0% to 100%),
2. Missing Keywords that are important for the job,
3. A concise Profile Summary highlighting the candidate's strengths,
4. A list of Technical Skills relevant to the job,
5. A list of Projects with "title" and "description" for each.
6. Provide feedback suggestions for each missing keyword.

Resume: {resume}
Job Description: {jd}

Your response must follow this exact JSON format:
{{
    "Job Description Match": "<percentage>%",
    "Missing Keywords": ["<keyword1>", "<keyword2>", ...],
    "Profile Summary": "<summary>",
    "Technical Skills": ["<skill1>", "<skill2>", ...],
    "Projects": [
        {{"title": "<project title>", "description": "<project description>"}} ,
        ...
    ],
    "Feedback Suggestions": {{
        "<keyword1>": "<suggestion for keyword1>",
        "<keyword2>": "<suggestion for keyword2>",
        ...
    }}
}}
"""

# Streamlit UI
def main():
    st.set_page_config(layout="wide")

    st.title("ATS Resume Tracking System")

    st.sidebar.title("Inputs")
    st.sidebar.write("Upload your resume and provide a job description to evaluate your compatibility.")

    # Input fields in sidebar
    uploaded_file = st.sidebar.file_uploader("Upload Resume (PDF only):", type=["pdf"])
    job_description = st.sidebar.text_area("Job Description:")
    submit = st.sidebar.button("Submit")

    if submit:
        if uploaded_file and job_description.strip():
            resume_text = extract_pdf_text(uploaded_file)
            input_prompt = prompt_template.format(resume=resume_text, jd=job_description)

            try:
                response = get_gemini_response(input_prompt)
                response_cleaned = re.sub(r'```json\s*|\s*```', '', response).strip()

                try:
                    parsed_response = json.loads(response_cleaned)

                    # Extract Data
                    job_description_match = parsed_response.get("Job Description Match", "0%")
                    missing_keywords = parsed_response.get("Missing Keywords", [])
                    profile_summary = parsed_response.get("Profile Summary", "No summary available.")
                    technical_skills = parsed_response.get("Technical Skills", [])
                    projects = parsed_response.get("Projects", [])
                    feedback_suggestions = parsed_response.get("Feedback Suggestions", {})

                    # Layout adjustment
                    st.header("ATS Analysis Results")
                    col1, col2 = st.columns([1, 1])

                    with col1:
                        st.subheader("Overall Performance")
                        match_percentage = int(job_description_match.replace('%', '').strip())
                        non_match_percentage = 100 - match_percentage
                        fig, ax = plt.subplots()
                        ax.pie([match_percentage, non_match_percentage],
                               labels=[f"Match {match_percentage}%", f"Non-Match {non_match_percentage}%"],
                               colors=['#8d99ae', '#003566'], autopct='%1.1f%%', startangle=90)
                        ax.axis('equal')
                        st.pyplot(fig)



                        st.subheader("Missing Keywords")
                        st.write(", ".join(missing_keywords) if missing_keywords else "No missing keywords.")

                        st.subheader("Feedback & Suggestions")
                        if missing_keywords:
                            for kw in missing_keywords:
                                suggestion = feedback_suggestions.get(kw, f"Expand details on {kw}.")
                                st.write(f"- For '{kw}': {suggestion}")
                        else:
                            st.write("Your resume covers all key areas well!")

                    with col2:
                        st.subheader ( "Technical Skills" )

                        if technical_skills:
                            # Divide the technical skills into 3 groups
                            skills_per_column=len ( technical_skills ) // 3
                            skills_groups=[technical_skills[i:i + skills_per_column] for i in
                                           range ( 0, len ( technical_skills ), skills_per_column )]

                            # Ensure the last group gets any remaining skills if the list isn't divisible by 3
                            while len ( skills_groups ) < 3:
                                skills_groups.append ( [] )

                            # Split the skills into 3 columns
                            colA, colB, colC=st.columns ( 3 )
                            with colA:
                                for skill in skills_groups[0]:
                                    st.write ( f"- {skill}" )
                            with colB:
                                for skill in skills_groups[1]:
                                    st.write ( f"- {skill}" )
                            with colC:
                                for skill in skills_groups[2]:
                                    st.write ( f"- {skill}" )
                        else:
                            st.write ( "No technical skills found." )


                        st.subheader("Projects")
                        if projects:
                            for project in projects:
                                title = project.get("title", "No Title Provided")
                                description = project.get("description", "No Description Available")
                                st.write(f"**{title}**")
                                st.write(f"Description: {description}")
                        else:
                            st.write("No projects identified.")

                        st.subheader("Profile Summary")
                        st.write(profile_summary)

                except json.JSONDecodeError:
                    st.error("Error: The response from Gemini is not valid JSON. Please check the raw response.")
                    st.error(f"Raw response: {response_cleaned}")

            except Exception as e:
                st.error("Error occurred while processing. Please try again.")
                st.error(f"Details: {e}")

        else:
            st.warning("Please upload a resume and provide a job description!")

if __name__ == "__main__":
    main()

