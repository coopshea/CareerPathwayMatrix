import os
import streamlit as st
import json
import pandas as pd
import numpy as np
from openai import OpenAI
import io
import tempfile
from datetime import datetime
import trafilatura

# Initialize the OpenAI client
# the newest OpenAI model is "gpt-4o" which was released May 13, 2024
# do not change this unless explicitly requested by the user
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def analyze_job_posting(job_text):
    """
    Analyze a job posting using OpenAI's API to extract key information.
    
    Args:
        job_text (str): The text content of the job posting
        
    Returns:
        dict: Extracted information about the job
    """
    try:
        prompt = f"""
        Analyze the following job posting content and extract key information:
        
        {job_text}
        
        Please extract and structure the following information in JSON format:
        1. job_title (the title of the position)
        2. company_name (the company offering the position)
        3. required_skills (list of technical and soft skills required)
        4. preferred_skills (list of preferred but not required skills)
        5. responsibilities (list of job responsibilities)
        6. experience_level (entry, mid, senior, executive)
        7. education_requirements (degrees, certifications required)
        8. industry (the industry this job belongs to)
        9. job_category (the general category of the job)
        10. remote_options (on-site, hybrid, remote)
        11. pathways (Which career pathways could this job lead to? List 3-5 potential future career paths)
        
        Format your response as a valid JSON object with these categories as keys.
        """
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        # Parse the JSON response
        job_data = json.loads(response.choices[0].message.content)
        return job_data
    except Exception as e:
        st.error(f"Error processing job posting: {str(e)}")
        return {}

def get_website_text_content(url):
    """
    Extract text content from a website URL.
    
    Args:
        url (str): The URL of the website to scrape
        
    Returns:
        str: The extracted text content
    """
    try:
        # Send a request to the website
        downloaded = trafilatura.fetch_url(url)
        text = trafilatura.extract(downloaded)
        return text
    except Exception as e:
        st.error(f"Error accessing website: {str(e)}")
        return ""

def convert_job_to_pathway(job_data):
    """
    Convert a job posting analysis into a pathway format compatible with our application.
    
    Args:
        job_data (dict): The job data extracted from analyze_job_posting
        
    Returns:
        dict: A pathway-formatted representation of the job
    """
    # Generate a unique ID for the job pathway
    job_id = f"job_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Map the job skills to pathway key skills
    required_skills = job_data.get("required_skills", [])
    preferred_skills = job_data.get("preferred_skills", [])
    
    # Ensure we're not dealing with None values
    if required_skills is None:
        required_skills = []
    if preferred_skills is None:
        preferred_skills = []
        
    key_skills = required_skills + preferred_skills
    
    # Generate a description for the pathway
    description = f"This pathway is based on a job posting for {job_data.get('job_title', 'Unknown Position')} at {job_data.get('company_name', 'Unknown Company')}. "
    
    # Safely get the required skills
    req_skills = job_data.get('required_skills', ['various skills'])
    if req_skills is None:
        req_skills = ['various skills']
    req_skills_text = ', '.join(req_skills[:3]) if req_skills else 'various skills'
    
    description += f"It requires experience in {req_skills_text}. "
    description += f"This is a {job_data.get('experience_level', 'mid-level')} position in the {job_data.get('industry', 'technology')} industry."
    
    # Create the metrics for the pathway (these are estimations)
    metrics = {
        "risk_level": {"value": 5, "sources": []},
        "success_probability": {"value": 7, "sources": []},
        "terminal_value": {"value": 6, "sources": []},
        "expected_value_10yr": {"value": 7, "sources": []},
        "capital_requirements": {"value": 4, "sources": []},
        "technical_specialization": {"value": 7, "sources": []},
        "network_dependency": {"value": 6, "sources": []},
        "time_to_return": {"value": 5, "sources": []},
        "control": {"value": 5, "sources": []},
        "optionality": {"value": 6, "sources": []}
    }
    
    # Adjust metrics based on job data
    if job_data.get("experience_level") == "senior" or job_data.get("experience_level") == "executive":
        metrics["terminal_value"]["value"] = 8
        metrics["technical_specialization"]["value"] = 9
    
    # Create the pathway object
    pathway = {
        "id": job_id,
        "name": f"{job_data.get('job_title', 'Job Opportunity')} - {job_data.get('company_name', 'Company')}",
        "category": job_data.get("job_category", "Job Opportunity"),
        "description": description,
        "target_customers": f"Professionals with {job_data.get('experience_level', 'relevant')} experience in {job_data.get('industry', 'the industry')}.",
        "success_examples": [f"{job_data.get('company_name', 'The company')} hiring for this position"],
        "key_skills": key_skills,
        "metrics": metrics,
        "rationale": {},
        "job_data": job_data  # Store the original job data for reference
    }
    
    return pathway

def add_job_posting_to_session(pathway):
    """
    Add a job posting pathway to the session state and database.
    
    Args:
        pathway (dict): The pathway to add
    """
    # Initialize the job pathways list if it doesn't exist
    if "job_pathways" not in st.session_state:
        st.session_state.job_pathways = []
    
    # Add the pathway to the list
    st.session_state.job_pathways.append(pathway)
    
    # Mark the pathway as highlighted in the session state
    st.session_state.highlighted_job = pathway["id"]
    
    # Add the job posting to the database
    from database import add_job_posting_to_db
    try:
        success = add_job_posting_to_db(pathway)
        if success:
            print(f"Successfully added job posting to database: {pathway['name']}")
        else:
            print(f"Failed to add job posting to database: {pathway['name']}")
    except Exception as e:
        print(f"Error adding job posting to database: {e}")
        # Continue even if database storage fails
        # The job will still be in the session state

def job_posting_page(pathways_df=None, metrics_data=None):
    """
    Streamlit page for adding job postings and converting them to pathways.
    
    Args:
        pathways_df (DataFrame): The pathways dataframe
        metrics_data (dict): Information about metrics
    """
    st.title("Add Job Posting")
    st.write("""
    Upload a job posting to analyze it and add it to your personalized career pathway analysis.
    The job posting will be highlighted in the 2x2 matrix visualization and you can generate a
    personalized roadmap to help you prepare for this specific job opportunity.
    """)
    
    # Create tabs for different input methods
    tab1, tab2, tab3 = st.tabs(["Upload Text", "Paste URL", "Enter Manually"])
    
    with tab1:
        st.write("## Upload Job Posting")
        st.write("Upload a job posting document (PDF, DOCX, or TXT)")
        
        uploaded_file = st.file_uploader("Upload job posting document", 
                                         type=["pdf", "docx", "txt"])
        
        if uploaded_file is not None:
            # Read the file content
            file_content = uploaded_file.read()
            
            # For PDFs and DOCXs, try to extract text (this is simplified)
            if uploaded_file.type == "application/pdf":
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                    temp_file.write(file_content)
                    temp_file_path = temp_file.name
                
                try:
                    import PyPDF2
                    with open(temp_file_path, 'rb') as pdf_file:
                        pdf_reader = PyPDF2.PdfReader(pdf_file)
                        file_content = ""
                        for page in pdf_reader.pages:
                            file_content += page.extract_text()
                except:
                    st.error("Unable to process PDF. Please try a text (.txt) file instead.")
                    file_content = ""
                
                # Clean up the temp file
                os.remove(temp_file_path)
            
            elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as temp_file:
                    temp_file.write(file_content)
                    temp_file_path = temp_file.name
                
                try:
                    import docx
                    doc = docx.Document(temp_file_path)
                    file_content = "\n".join([para.text for para in doc.paragraphs])
                except:
                    st.error("Unable to process DOCX. Please try a text (.txt) file instead.")
                    file_content = ""
                
                # Clean up the temp file
                os.remove(temp_file_path)
            
            else:  # Text file
                file_content = file_content.decode('utf-8')
            
            st.write("### Job Posting Preview")
            preview = file_content[:1000] + "..." if len(file_content) > 1000 else file_content
            st.text_area("Preview of the job posting:", preview, height=200, key="preview_upload")
            
            if st.button("Analyze Job Posting", key="analyze_upload"):
                with st.spinner("Analyzing the job posting..."):
                    # Process the job posting
                    job_data = analyze_job_posting(file_content)
                    
                    if job_data:
                        # Convert the job data to a pathway
                        pathway = convert_job_to_pathway(job_data)
                        
                        # Add the pathway to the session state
                        add_job_posting_to_session(pathway)
                        
                        # Show success message with option to generate roadmap
                        st.success(f"Successfully added job posting for {job_data.get('job_title')} at {job_data.get('company_name')}!")
                        
                        if st.button("Generate AI Roadmap for This Job", key="gen_roadmap_upload"):
                            # Set a session state variable to indicate we want to switch to the AI roadmap tab
                            st.session_state.generate_roadmap_for = pathway
                            # Switch to the AI roadmap tab (index 3)
                            st.experimental_set_query_params(tab="AI Roadmap Generator")
                            st.rerun()
    
    with tab2:
        st.write("## Paste Job Posting URL")
        st.write("Enter the URL of a job posting to analyze")
        
        url = st.text_input("Job Posting URL", "", key="job_url")
        
        if url:
            if st.button("Fetch and Analyze", key="fetch_url"):
                with st.spinner("Fetching content from URL..."):
                    # Get the text content from the URL
                    text_content = get_website_text_content(url)
                    
                    if text_content:
                        st.write("### Job Posting Preview")
                        preview = text_content[:1000] + "..." if len(text_content) > 1000 else text_content
                        st.text_area("Preview of the job posting:", preview, height=200, key="preview_url")
                        
                        # Process the job posting
                        job_data = analyze_job_posting(text_content)
                        
                        if job_data:
                            # Convert the job data to a pathway
                            pathway = convert_job_to_pathway(job_data)
                            
                            # Add the pathway to the session state
                            add_job_posting_to_session(pathway)
                            
                            # Show success message with option to generate roadmap
                            st.success(f"Successfully added job posting for {job_data.get('job_title')} at {job_data.get('company_name')}!")
                            
                            if st.button("Generate AI Roadmap for This Job", key="gen_roadmap_url"):
                                # Set a session state variable to indicate we want to switch to the AI roadmap tab
                                st.session_state.generate_roadmap_for = pathway
                                # Switch to the AI roadmap tab (index 3)
                                st.experimental_set_query_params(tab="AI Roadmap Generator")
                                st.rerun()
                    else:
                        st.error("Could not extract content from the provided URL. Please check the URL or try another input method.")
    
    with tab3:
        st.write("## Enter Job Posting Details Manually")
        st.write("Fill in the details of the job posting")
        
        # Create a form for manual entry
        job_title = st.text_input("Job Title", "", key="job_title_input")
        company_name = st.text_input("Company Name", "", key="company_name_input")
        industry = st.text_input("Industry", "", key="industry_input")
        job_category = st.text_input("Job Category", "", key="job_category_input")
        
        experience_level = st.selectbox(
            "Experience Level",
            ["entry", "mid", "senior", "executive"],
            key="experience_level_select"
        )
        
        remote_options = st.selectbox(
            "Remote Options",
            ["on-site", "hybrid", "remote"],
            key="remote_options_select"
        )
        
        required_skills = st.text_area("Required Skills (one per line)", "", key="required_skills_area")
        preferred_skills = st.text_area("Preferred Skills (one per line)", "", key="preferred_skills_area")
        responsibilities = st.text_area("Job Responsibilities (one per line)", "", key="responsibilities_area")
        education = st.text_area("Education Requirements", "", key="education_area")
        
        if st.button("Create Job Pathway", key="create_manual"):
            # Convert text areas to lists
            required_skills_list = [skill.strip() for skill in required_skills.split("\n") if skill.strip()]
            preferred_skills_list = [skill.strip() for skill in preferred_skills.split("\n") if skill.strip()]
            responsibilities_list = [resp.strip() for resp in responsibilities.split("\n") if resp.strip()]
            
            # Create job data dictionary
            job_data = {
                "job_title": job_title,
                "company_name": company_name,
                "required_skills": required_skills_list,
                "preferred_skills": preferred_skills_list,
                "responsibilities": responsibilities_list,
                "experience_level": experience_level,
                "education_requirements": education,
                "industry": industry,
                "job_category": job_category,
                "remote_options": remote_options,
                "pathways": []  # This would be filled by AI in the analyze_job_posting function
            }
            
            # Convert the job data to a pathway
            pathway = convert_job_to_pathway(job_data)
            
            # Add the pathway to the session state
            add_job_posting_to_session(pathway)
            
            # Show success message with option to generate roadmap
            st.success(f"Successfully added job posting for {job_title} at {company_name}!")
            
            if st.button("Generate AI Roadmap for This Job", key="gen_roadmap_manual"):
                # Set a session state variable to indicate we want to switch to the AI roadmap tab
                st.session_state.generate_roadmap_for = pathway
                # Switch to the AI roadmap tab (index 3)
                st.experimental_set_query_params(tab="AI Roadmap Generator")
                st.rerun()