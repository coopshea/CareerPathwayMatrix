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
from database import add_job_posting_to_db

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
        
        Please extract and return the following information in JSON format:
        - title: the job title
        - company: the company name
        - category: job category (e.g., Software Engineering, Data Science, Marketing)
        - industry: the industry
        - seniority: seniority level (e.g., Entry, Mid-level, Senior)
        - required_skills: a list of required skills mentioned in the posting
        - preferred_skills: a list of preferred/nice-to-have skills mentioned
        - responsibilities: a list of key responsibilities
        - education: education requirements
        - experience: experience requirements
        - salary_range: salary range (if provided)
        - location: job location or remote status
        - related_pathways: suggest 2-3 potential career pathways this job might be part of
        
        Format your response as valid JSON.
        """
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a skilled job analyst who extracts structured information from job postings."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        # Parse the JSON response
        result = json.loads(response.choices[0].message.content)
        return result
    
    except Exception as e:
        st.error(f"Error analyzing job posting: {str(e)}")
        return None

def get_website_text_content(url):
    """
    Extract text content from a website URL.
    
    Args:
        url (str): The URL of the website to scrape
        
    Returns:
        str: The extracted text content
    """
    try:
        # Download the content
        downloaded = trafilatura.fetch_url(url)
        
        # Extract the main text
        text = trafilatura.extract(downloaded)
        
        if not text:
            # If trafilatura fails, try a more basic approach
            import requests
            from bs4 import BeautifulSoup
            
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()
            
            # Get text
            text = soup.get_text()
            
            # Break into lines and remove leading and trailing space
            lines = (line.strip() for line in text.splitlines())
            # Break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            # Drop blank lines
            text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text
    
    except Exception as e:
        st.error(f"Error extracting text from website: {str(e)}")
        return None

def convert_job_to_pathway(job_data):
    """
    Convert a job posting analysis into a pathway format compatible with our application.
    
    Args:
        job_data (dict): The job data extracted from analyze_job_posting
        
    Returns:
        dict: A pathway-formatted representation of the job
    """
    # Generate a unique ID for the pathway
    import hashlib
    import time
    unique_id = hashlib.md5(f"{job_data.get('title', '')}-{job_data.get('company', '')}-{time.time()}".encode()).hexdigest()[:10]
    
    # Compile the key skills
    key_skills = []
    if 'required_skills' in job_data and job_data['required_skills']:
        for skill in job_data['required_skills']:
            key_skills.append({
                "name": skill,
                "type": "required",
                "description": ""
            })
    
    if 'preferred_skills' in job_data and job_data['preferred_skills']:
        for skill in job_data['preferred_skills']:
            key_skills.append({
                "name": skill,
                "type": "preferred",
                "description": ""
            })
    
    # Create example metrics for the pathway
    # In a real implementation, these would be derived more intelligently
    metrics = {
        "growth_potential": 70,  # Percentage scores
        "job_satisfaction": 75,
        "skill_match": 65,
        "work_life_balance": 60
    }
    
    # Success examples
    success_examples = [{
        "title": "Success Path",
        "description": f"Candidates who excel in this {job_data.get('title', 'role')} typically have strong backgrounds in {', '.join(job_data.get('required_skills', ['relevant skills'])[:3])}."
    }]
    
    # Construct the pathway
    pathway = {
        "id": f"job-{unique_id}",
        "name": f"{job_data.get('title', 'Job')} at {job_data.get('company', 'Company')}",
        "category": job_data.get('category', 'Uncategorized'),
        "description": f"Job posting for {job_data.get('title', 'position')} at {job_data.get('company', 'company')}.\n\n" + 
                      f"Industry: {job_data.get('industry', 'Not specified')}\n" +
                      f"Experience Level: {job_data.get('seniority', 'Not specified')}\n" +
                      f"Location: {job_data.get('location', 'Not specified')}",
        "target_customers": "Job seekers interested in this position",
        "success_examples": success_examples,
        "key_skills": key_skills,
        "metrics": metrics,
        "rationale": {
            "why": f"This job posting was added to help you understand the requirements for a {job_data.get('title', 'position')} role.",
            "how": "By analyzing the job requirements, you can identify skill gaps and create a plan to acquire the necessary skills.",
            "what": f"This pathway represents a real job posting for {job_data.get('title', 'a position')} at {job_data.get('company', 'a company')}."
        },
        "is_job_posting": True,
        "job_data": job_data,
        "date_added": datetime.now().isoformat()
    }
    
    return pathway

def add_job_posting_to_session(pathway):
    """
    Add a job posting pathway to the session state and database.
    
    Args:
        pathway (dict): The pathway to add
    """
    # Add to session state
    if 'job_pathways' not in st.session_state:
        st.session_state.job_pathways = []
    
    # Check if already exists
    for i, existing_pathway in enumerate(st.session_state.job_pathways):
        if existing_pathway.get('id') == pathway.get('id'):
            # Replace existing
            st.session_state.job_pathways[i] = pathway
            break
    else:
        # Add new
        st.session_state.job_pathways.append(pathway)
    
    # Add to database
    try:
        add_job_posting_to_db(pathway)
    except Exception as e:
        st.warning(f"Could not save job posting to database: {e}")

def render_job_postings_tab(user_data=None, selectbox=None, file_uploader=None):
    """
    Render the job postings tab with the provided user data
    
    Args:
        user_data: The user data object
        selectbox: Function to create a selectbox
        file_uploader: Function to create a file uploader
    """
    # For backward compatibility, call the existing implementation
    job_posting_page(is_merged_view=True)

def job_posting_page(pathways_df=None, metrics_data=None, is_merged_view=False):
    """
    Streamlit page for adding job postings and converting them to pathways.
    
    Args:
        pathways_df (DataFrame): The pathways dataframe
        metrics_data (dict): Information about metrics
        is_merged_view (bool): Whether this is being shown in the merged Job & Resume tab
    """
    # Skip the title and intro if this is part of the merged view
    if not is_merged_view:
        st.title("Job Posting Analysis")
        st.write("""
        Upload a job description or provide a link to a job posting, and our AI will analyze the requirements
        and add it as a pathway in the system.
        """)
    
    # Job posting input - either text or file upload
    input_method = st.radio("How would you like to input the job posting?", 
                          ["Text", "File Upload", "Website URL"],
                          key=f"job_input_method{'_merged' if is_merged_view else ''}")
    
    job_text = None
    
    if input_method == "Text":
        job_text = st.text_area("Paste the job posting text here", height=200 if is_merged_view else 300,
                               key=f"job_text{'_merged' if is_merged_view else ''}")
    
    elif input_method == "File Upload":
        uploaded_file = st.file_uploader("Upload a job posting document", 
                                      type=["pdf", "docx", "txt"],
                                      key=f"job_file{'_merged' if is_merged_view else ''}")
        
        if uploaded_file:
            # Process the file based on type
            if uploaded_file.type == "application/pdf":
                try:
                    import PyPDF2
                    # Save the uploaded file temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                        temp_file.write(uploaded_file.read())
                        temp_file_path = temp_file.name
                    
                    # Extract text from the PDF
                    with open(temp_file_path, 'rb') as file:
                        pdf_reader = PyPDF2.PdfReader(file)
                        job_text = ""
                        for page_num in range(len(pdf_reader.pages)):
                            job_text += pdf_reader.pages[page_num].extract_text()
                    
                    # Clean up the temporary file
                    os.remove(temp_file_path)
                    
                except Exception as e:
                    st.error(f"Error processing PDF: {e}")
            
            elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                try:
                    import docx
                    # Save the uploaded file temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as temp_file:
                        temp_file.write(uploaded_file.read())
                        temp_file_path = temp_file.name
                    
                    # Extract text from the DOCX
                    doc = docx.Document(temp_file_path)
                    job_text = "\n".join([para.text for para in doc.paragraphs])
                    
                    # Clean up the temporary file
                    os.remove(temp_file_path)
                    
                except Exception as e:
                    st.error(f"Error processing DOCX: {e}")
            
            else:  # Text file
                job_text = uploaded_file.read().decode('utf-8')
    
    elif input_method == "Website URL":
        url = st.text_input("Enter the URL of the job posting", 
                         key=f"job_url{'_merged' if is_merged_view else ''}")
        
        if url and st.button("Fetch Content", key=f"fetch_btn{'_merged' if is_merged_view else ''}"):
            with st.spinner("Fetching content from website..."):
                try:
                    job_text = get_website_text_content(url)
                    if job_text:
                        st.success("Content fetched successfully!")
                    else:
                        st.error("Could not extract content from the provided URL.")
                except Exception as e:
                    st.error(f"Error fetching content: {e}")
    
    # Display a preview of the job text if available
    if job_text:
        # Use a smaller preview in merged view
        preview_length = 500 if is_merged_view else 1000
        
        with st.expander("Preview of job posting text"):
            st.text(job_text[:preview_length] + ("..." if len(job_text) > preview_length else ""))
        
        # Save to session state
        st.session_state.job_posting_text = job_text
        
        # Button to analyze the job posting
        if st.button("Analyze Job Posting", key=f"analyze_btn{'_merged' if is_merged_view else ''}"):
            with st.spinner("Analyzing job posting..."):
                try:
                    # Call the function to analyze the job posting
                    analysis = analyze_job_posting(job_text)
                    
                    # Convert to pathway format
                    pathway = convert_job_to_pathway(analysis)
                    
                    # Add the pathway to the session state and database
                    add_job_posting_to_session(pathway)
                    
                    # Display summary
                    st.success("Job posting analyzed and added as a pathway!")
                    
                    # More compact display in merged view
                    st.write("### Job Analysis Summary")
                    st.write(f"**Job Title:** {analysis.get('title', 'Unknown')}")
                    st.write(f"**Company:** {analysis.get('company', 'Unknown')}")
                    st.write(f"**Category:** {analysis.get('category', 'Unknown')}")
                    
                    # Required skills - more compact in merged view
                    if is_merged_view:
                        skills_col1, skills_col2 = st.columns(2)
                        with skills_col1:
                            st.write("**Required Skills:**")
                            for skill in analysis.get('required_skills', [])[:5]:  # Limit to top 5 in merged view
                                st.write(f"- {skill}")
                            if len(analysis.get('required_skills', [])) > 5:
                                st.write(f"- *and {len(analysis.get('required_skills', [])) - 5} more*")
                        
                        with skills_col2:
                            if analysis.get('preferred_skills'):
                                st.write("**Preferred Skills:**")
                                for skill in analysis.get('preferred_skills', [])[:5]:  # Limit to top 5
                                    st.write(f"- {skill}")
                                if len(analysis.get('preferred_skills', [])) > 5:
                                    st.write(f"- *and {len(analysis.get('preferred_skills', [])) - 5} more*")
                    else:
                        # Full display in standalone view
                        st.write("#### Required Skills")
                        for skill in analysis.get('required_skills', []):
                            st.write(f"- {skill}")
                        
                        # Preferred skills
                        if analysis.get('preferred_skills'):
                            st.write("#### Preferred Skills")
                            for skill in analysis.get('preferred_skills', []):
                                st.write(f"- {skill}")
                    
                    # Store in session state for resume skill comparison
                    st.session_state.job_skills = {
                        'required': analysis.get('required_skills', []),
                        'preferred': analysis.get('preferred_skills', [])
                    }
                    
                    # In merged view, show combined analysis notification if resume is also processed
                    if is_merged_view and 'user_resume_skills' in st.session_state:
                        st.info("Job posting and resume both analyzed! Check below for combined analysis.")
                    
                    # Button to view the pathway in the Find Your Pathway tab
                    if st.button("View in Pathways", key=f"view_pathway_btn{'_merged' if is_merged_view else ''}"):
                        # Set the session state to navigate to the pathways tab
                        st.session_state.active_tab = 7  # Index of the Find Your Pathway tab (updated for reordering)
                        st.rerun()
                
                except Exception as e:
                    st.error(f"Error analyzing job posting: {e}")
                    st.info("Try with a different job posting or check your connection.")
    else:
        st.info("Please input a job posting using one of the methods above to analyze it.")