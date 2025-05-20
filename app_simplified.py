import streamlit as st

# Set page config at the very beginning
st.set_page_config(page_title="CareerPath Navigator", layout="wide")

from dataclasses import dataclass, asdict, field
from typing import Optional, Dict, Any, List
import time
import os
from openai import OpenAI

from data import load_data
from visualizations import create_matrix_visualization
from recommendations import calculate_pathway_matches
from skill_graph import skill_graph_page
from utils import create_pathway_card, DEFAULT_IMAGES

# 1) Central container for all user inputs & uploads
@dataclass
class UserData:
    resume_bytes: Optional[bytes] = None
    job_bytes: Optional[bytes] = None
    portfolio_bytes: Optional[bytes] = None
    questionnaire: Dict[str, Any] = field(default_factory=dict)
    selected_pathway: Optional[str] = None

if "user_data" not in st.session_state:
    st.session_state.user_data = UserData()

# 2) Widget factories to guarantee unique keys
def sb(label: str, options: List[Any], default: int = 0, key: str = ""):
    return st.selectbox(label, options, index=default, key=key)

def fu(label: str, types: List[str], key: str):
    return st.file_uploader(label, type=types, key=key)

# 3) Load static data once
@st.cache_data
def load_all():
    return load_data()

pathways_df, metrics_data, categories = load_all()

# AI Chat Assistant Implementation
def render_ai_chat_assistant():
    st.write("### AI Career Assistant")
    
    # Show disclaimer
    st.markdown("""
    ℹ️ **Disclaimer**
    
    This AI assistant can provide guidance about CareerPath Navigator features and career advice.
    It has a limit of 10 messages per session to ensure fair usage.
    """)
    
    # Add caveat below the chat assistant
    st.warning("**FUNCTIONAL PROTOTYPE** - This application demonstrates core functionality (AI integration, skills extraction, etc). UI/UX design is not finalized.")
    
    # Initialize message counter
    if 'message_count' not in st.session_state:
        st.session_state.message_count = 0
        st.session_state.last_reset_time = time.time()
    
    # Initialize reflective questions sequence
    if "reflective_questions" not in st.session_state:
        st.session_state.reflective_questions = [
            "What are your biggest strengths professionally? Think about what others consistently praise you for.",
            "Which skills do you most enjoy using in your work or projects?",
            "What aspects of your current or past roles have felt most meaningful to you?",
            "Imagine your ideal workday - what activities would you be doing?",
            "What values are most important to you in your work environment?",
            "What obstacles seem to consistently appear in your career path?",
            "If resources and time weren't factors, what career path would you pursue?",
            "What specific impact do you want to make through your work?"
        ]
        st.session_state.current_reflective_q = 0
        st.session_state.reflective_mode = False
        st.session_state.reflective_responses = {}
    
    # Check if 30 minutes have passed since the last reset
    current_time = time.time()
    if current_time - st.session_state.last_reset_time > 1800:  # 1800 seconds = 30 minutes
        st.session_state.message_count = 0
        st.session_state.last_reset_time = current_time
    
    # Display remaining messages counter
    remaining_messages = max(0, 10 - st.session_state.message_count)
    if remaining_messages < 3:
        st.warning(f"**Rate limit:** {remaining_messages}/10 messages left for this session. Resets in {30 - int((current_time - st.session_state.last_reset_time)/60)} minutes.")
    else:
        st.info(f"**Messages remaining:** {remaining_messages}/10 for this session. Resets every 30 minutes.")
    
    # Option to start reflective journey
    if not st.session_state.reflective_mode:
        if st.button("Start Career Reflection Journey", key="start_reflection"):
            st.session_state.reflective_mode = True
            # Add the first reflection question as an assistant message
            first_question = st.session_state.reflective_questions[0]
            if 'messages' not in st.session_state:
                st.session_state.messages = []
            st.session_state.messages.append({"role": "assistant", "content": f"**Career Reflection:** {first_question}"})
            st.rerun()
    
    # Initialize chat messages if not already in session state
    if "messages" not in st.session_state:
        # Create a greeting message
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I'm your AI career assistant. To get the most out of CareerPath Navigator, I recommend:\n\n1. Fill out the career preferences questionnaire in the 'Find Your Pathway' tab\n2. Upload your resume in the 'Skill Graph' tab for skill analysis\n3. Return here for personalized career guidance based on your profile\n\nHow can I help you today?"}
        ]
    
    # Display chat messages from history on app rerun
    if 'messages' in st.session_state:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    # Accept user input
    if prompt := st.chat_input("Share your thoughts or ask a question..."):
        # Check rate limit
        if st.session_state.message_count >= 10:
            with st.chat_message("assistant"):
                st.error("You've reached the maximum number of messages for this session. Please wait for the rate limit to reset.")
            return
        
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Increment message counter
        st.session_state.message_count += 1
        
        # Handle the response differently based on mode
        if st.session_state.reflective_mode:
            # Save the response to the session state
            try:
                # Get the current question
                current_q = st.session_state.reflective_questions[st.session_state.current_reflective_q]
                
                # Store the response
                st.session_state.reflective_responses[current_q] = prompt
                
                # Move to the next question
                st.session_state.current_reflective_q += 1
                
                # Create a placeholder for the assistant's response
                with st.chat_message("assistant"):
                    response_placeholder = st.empty()
                    
                    # If there are more questions, ask the next one
                    if st.session_state.current_reflective_q < len(st.session_state.reflective_questions):
                        next_q = st.session_state.reflective_questions[st.session_state.current_reflective_q]
                        response = f"Thank you for sharing that. Let's continue with another reflection: **{next_q}**"
                    else:
                        # End of reflective questions
                        response = "Thank you for completing the career reflection! I've recorded your responses, which will help personalize your career guidance. Is there anything specific you'd like to explore now based on your reflections?"
                        st.session_state.reflective_mode = False
                        
                    # Display the response
                    response_placeholder.markdown(response)
                
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": response})
                
            except Exception as e:
                with st.chat_message("assistant"):
                    response = f"I appreciate your response. There was a technical issue, but we can continue our conversation. What else would you like to discuss about your career journey?"
                    st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                print(f"Error in reflective mode: {e}")
        else:
            # Normal chat mode - process the user's question
            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                
                # Stream the response from API
                full_response = stream_ai_response(prompt, response_placeholder)
                
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": full_response})
    
    # Add controls for reflective mode
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Clear Chat", key="clear_chat"):
            st.session_state.messages = []
            st.session_state.current_reflective_q = 0
            st.session_state.reflective_mode = False
            st.session_state.reflective_responses = {}
            st.rerun()
    
    with col2:
        if not st.session_state.reflective_mode and st.button("New Reflection", key="new_reflection"):
            st.session_state.current_reflective_q = 0
            st.session_state.reflective_mode = True
            # Add the first reflection question
            first_question = st.session_state.reflective_questions[0]
            st.session_state.messages.append({"role": "assistant", "content": f"**Career Reflection:** {first_question}"})
            st.rerun()

# Stream AI-powered response with word-by-word display
def stream_ai_response(question, placeholder):
    """Generate and stream an AI-powered response using OpenAI API"""
    # Handle None case
    if question is None:
        default_response = "I can help you explore different career paths and develop your skills. What would you like to know?"
        placeholder.markdown(default_response)
        return default_response
        
    try:
        # Get the API key from environment variable
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            fallback = "I couldn't access the OpenAI API key. Please provide a valid API key to enable AI-powered responses."
            placeholder.markdown(fallback)
            return fallback
        
        # Create OpenAI client
        client = OpenAI(api_key=api_key)
        
        # System message for the chat context
        system_message = """You are a helpful career assistant in the CareerPath Navigator application. 
        You should encourage users to:
        1. Fill out the career preferences questionnaire in the 'Find Your Pathway' tab
        2. Upload their resume in the 'Skill Graph' tab for skill analysis
        3. Return to chat for personalized guidance based on their profile
        
        You can guide users to different features:
        - 2x2 Matrix (tab 5): For comparing career paths visually
        - Find Your Pathway (tab 6): For matching preferences to careers
        - AI Roadmap (tab 2): For generating AI-powered personalized roadmaps
        - Job & Resume Analysis (tab 1): For analyzing job opportunities
        - Skill Graph (tab 3): For analyzing user skills and gaps
        - Project Portfolio (tab 4): For managing projects
        
        Keep responses friendly, concise and helpful. Always recommend the appropriate tool
        based on what the user is trying to accomplish.
        """
        
        # Convert and stream the response
        full_response = ""
        response = client.chat.completions.create(
            model="gpt-4o",  # Using the latest model
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": question}
            ],
            stream=True
        )
        
        # Process the streaming response
        for chunk in response:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_response += content
                placeholder.markdown(full_response + "▌")
        
        # Display final response
        placeholder.markdown(full_response)
        return full_response
        
    except Exception as e:
        # Fallback response for errors
        error_response = f"I'm having trouble generating a response right now. Please try again later. Error: {str(e)}"
        placeholder.markdown(error_response)
        return error_response

# Function to provide quick responses based on keywords (backup if AI fails)
def get_quick_response(question):
    """Provide quick responses based on keywords for low latency"""
    question = question.lower()
    
    if "hello" in question or "hi" in question:
        return "Hello! How can I help with your career development today?"
    
    if "thank" in question:
        return "You're welcome! Feel free to ask if you have any other questions."
    
    if any(word in question for word in ["resume", "cv"]):
        return "You can upload your resume in the 'Job & Resume Analysis' tab to get personalized insights about your skills and experience."
    
    if any(word in question for word in ["job", "posting", "opportunity"]):
        return "To analyze job postings, head to the 'Job & Resume Analysis' tab where you can paste job descriptions or enter URLs to extract requirements and match them against your skills."
    
    if any(word in question for word in ["roadmap", "plan", "next steps"]):
        return "For a personalized career roadmap, check the 'AI Roadmap' tab. You can select a pathway and get AI-generated steps to achieve your goals."
    
    if any(word in question for word in ["skill", "expertise", "abilities"]):
        return "The 'Skill Graph' tab will analyze your skills, identify gaps, and suggest improvements based on job market demands."
    
    if any(word in question for word in ["compare", "matrix", "options"]):
        return "Use the '2x2 Matrix' tab to visually compare different career pathways based on metrics that matter to you."
    
    if any(word in question for word in ["pathway", "route", "career path"]):
        return "The 'Find Your Pathway' tab helps match your preferences to potential career paths. Fill out the questionnaire to see personalized recommendations."
    
    # Default response
    return "I'm here to help with your career development. You can explore different pathways, analyze job postings, create roadmaps, and more. What would you like to focus on today?"

# 4) Page‐by‐page renderers
def render_welcome_tab():
    st.header("🚀 Welcome to CareerPath Navigator")
    
    # Motivational introduction
    st.markdown("""
    ### Finding Your Path Forward
    
    Feeling stuck in your current role? Excited about exploring a new industry but not sure where to start? 
    
    **CareerPath Navigator** is designed for professionals just like you - helping you bridge the gap between 
    where you are now and where you want to be.
    
    ### How to Use This App:
    
    1. **Explore** career pathways using the **2×2 Matrix** tab
    2. **Analyze** your current skills with the **Skill Graph** tab 
    3. **Discover** matching careers in the **Find Your Pathway** tab
    4. **Plan** your journey with the **AI Roadmap** tab
    5. **Compare** your skills to opportunities in the **Job & Resume Analysis** tab
    
    Every journey begins with a single step. Use the tabs above to navigate through the features or ask our 
    AI assistant below for personalized guidance.
    """)
    
    # AI chat assistant
    st.markdown("---")
    st.markdown("### Not sure where to start? Ask our AI Career Assistant")
    
    # AI chat assistant
    render_ai_chat_assistant()

def render_portfolio_tab():
    st.header("📂 Project Portfolio")
    b = fu("Upload project doc/image", ["pdf","docx","txt","jpg","png"], key="portfolio_upload")
    if b: 
        st.session_state.user_data.portfolio_bytes = b.read()
        st.success("Portfolio file saved.")

def render_2x2_matrix_tab():
    st.header("🔢 2×2 Matrix")
    # Choose axes
    cols = st.columns(2)
    with cols[0]:
        x_metric = sb("X‐Axis", list(metrics_data.keys()), key="matrix_x")
    with cols[1]:
        y_metric = sb("Y‐Axis", list(metrics_data.keys()), key="matrix_y")
    
    # Create visualization
    create_matrix_visualization(pathways_df, x_metric, y_metric, metrics_data)

def render_find_pathway_tab():
    st.header("🔍 Find Your Pathway")
    
    st.write("""
    Complete the questionnaire below to discover career pathways that align with your preferences.
    """)
    
    # Create the questionnaire
    st.subheader("Career Preferences Questionnaire")
    
    metrics = metrics_data.keys()
    user_preferences = {}
    importance_weights = {}
    
    # Create columns for better layout
    col1, col2 = st.columns(2)
    
    metric_count = 0
    for metric_id in metrics:
        metric_info = metrics_data[metric_id]
        
        # Alternate between columns
        with col1 if metric_count % 2 == 0 else col2:
            st.markdown(f"##### {metric_info['name']}")
            st.caption(metric_info['description'])
            
            # Create a slider for preference
            preference = st.slider(
                f"Your preference ({metric_info['low_label']} to {metric_info['high_label']})",
                1, 10, 5, 
                key=f"pref_{metric_id}"
            )
            
            # Create a slider for importance
            importance = st.slider(
                "How important is this to you?",
                1, 10, 5,
                key=f"imp_{metric_id}"
            )
            
            # Store the values - use format expected by calculate_pathway_matches
            user_preferences[metric_id] = [max(1, preference-1), min(10, preference+1)]
            importance_weights[metric_id] = importance
            
            metric_count += 1
    
    # Calculate matches when button is clicked
    if st.button("Find Matching Pathways", key="find_pathways_btn"):
        matches = calculate_pathway_matches(pathways_df, user_preferences, importance_weights)
        
        st.session_state.pathway_matches = matches
        
        # Display the matches
        st.markdown("## Best Matching Pathways")
        for pathway_id, score, explanation in matches[:5]:
            pathway = next((p for p in pathways_df if p["id"] == pathway_id), None)
            if pathway:
                st.markdown(f"### {pathway['name']} (Match: {score:.0f}%)")
                st.markdown(explanation)
                
                # Show more details with an expander
                with st.expander("View Details"):
                    st.markdown(f"**Description:** {pathway['description']}")
                    
                    st.markdown("**Key Skills:**")
                    for skill in pathway.get('key_skills', []):
                        st.markdown(f"- {skill}")
                    
                    # Add a button to generate a roadmap for this pathway
                    if st.button("Generate Roadmap", key=f"gen_road_{pathway_id}"):
                        st.session_state.user_data.selected_pathway = pathway_id
                        st.session_state.active_tab = 2  # AI Roadmap tab
                        st.rerun()

def render_ai_roadmap_tab():
    st.header("🤖 AI Career Roadmap")
    
    from ai_roadmap import ai_roadmap_generator_page
    
    # Get the selected pathway if available
    pre_selected_pathway = None
    if st.session_state.user_data.selected_pathway:
        pathway_id = st.session_state.user_data.selected_pathway
        for p in pathways_df:
            if p["id"] == pathway_id:
                pre_selected_pathway = p
                break
    
    # Pass the pre-selected pathway to the roadmap generator
    ai_roadmap_generator_page(pre_selected_pathway, pathways_df, metrics_data)

def render_job_resume_tab():
    st.header("📑 Job & Resume Analysis")
    
    st.write("""
    Upload your resume and job descriptions to analyze the alignment between your skills and job requirements.
    This analysis helps identify which skills are worth learning first and provides valuable context for personalized career guidance.
    """)
    
    # Create tabs for file upload and manual entry
    file_tab, questionnaire_tab = st.tabs(["Upload Documents", "Fill Questionnaire"])
    
    with file_tab:
        # Create columns for side-by-side layout
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Resume Analysis")
            st.write("Upload your resume to extract and analyze your skills")
            
            # Resume upload
            resume_file = fu("Upload your resume (PDF, DOCX, or TXT)", 
                            ["pdf", "docx", "txt"],
                            key="resume_upload")
            
            if resume_file:
                # Process resume
                file_content = resume_file.read()
                st.session_state.user_data.resume_bytes = file_content
                
                # Extract text based on file type
                resume_text = ""
                try:
                    if resume_file.type == "application/pdf":
                        # Process PDF
                        import io
                        from PyPDF2 import PdfReader
                        pdf_reader = PdfReader(io.BytesIO(file_content))
                        for page in pdf_reader.pages:
                            resume_text += page.extract_text() + "\n"
                    
                    elif resume_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                        # Process DOCX
                        import io
                        from docx import Document
                        doc = Document(io.BytesIO(file_content))
                        resume_text = "\n".join([para.text for para in doc.paragraphs])
                    
                    else:
                        # Process as plain text
                        resume_text = file_content.decode("utf-8")
                        
                    st.success("Resume uploaded successfully!")
                    
                    # Show extracted text in expander
                    with st.expander("View Extracted Text"):
                        st.text(resume_text)
                        
                    # Store in session state
                    st.session_state.resume_text = resume_text
                    
                except Exception as e:
                    st.error(f"Error processing file: {str(e)}")
            
            # Process resume button
            if st.button("Analyze Skills & Experience", key="analyze_resume_btn"):
                if 'resume_text' in st.session_state and st.session_state.resume_text:
                    with st.spinner("Analyzing your resume..."):
                        # Call skill extraction function
                        from skill_graph import analyze_resume_skills
                        try:
                            # Try using AI for skill extraction
                            skills_dict = analyze_resume_skills(st.session_state.resume_text)
                            st.session_state.extracted_skills = skills_dict
                            st.success("Skills extracted successfully!")
                            
                            # Display key skills
                            st.subheader("Key Skills Identified")
                            
                            for skill, details in skills_dict.items():
                                rating = details.get('rating', 3)
                                st.markdown(f"**{skill}** - Proficiency: {'⭐' * rating}")
                            
                        except Exception as e:
                            # Fallback to sample skills on API error
                            from skill_graph import get_sample_skills
                            st.warning(f"Using sample skills data. Error: {str(e)}")
                            st.session_state.extracted_skills = get_sample_skills()
                            
                            # Display key skills
                            st.subheader("Sample Skills (Replace with your actual skills)")
                            
                            for skill, details in st.session_state.extracted_skills.items():
                                rating = details.get('rating', 3)
                                st.markdown(f"**{skill}** - Proficiency: {'⭐' * rating}")
                else:
                    st.warning("Please upload a resume first.")
        
        with col2:
            st.subheader("Job Posting Analysis")
            st.write("Analyze job postings to extract key requirements")
            
            # Job posting input
            job_text = st.text_area("Paste job description text here:", height=200, key="job_text")
            job_url = st.text_input("Or enter job posting URL:", key="job_url")
            
            if st.button("Analyze Job Requirements", key="analyze_job_btn"):
                with st.spinner("Analyzing job requirements..."):
                    # Call job analysis function
                    from job_postings_merged import analyze_job_posting, get_website_text_content
                    
                    # Get job text from URL if provided
                    if job_url and not job_text:
                        try:
                            job_text = get_website_text_content(job_url)
                            st.success(f"Successfully extracted content from URL")
                        except Exception as e:
                            st.error(f"Error extracting content from URL: {str(e)}")
                            st.session_state.job_data = None
                    
                    if job_text:
                        try:
                            # Analyze job posting
                            job_data = analyze_job_posting(job_text)
                            st.session_state.job_data = job_data
                            st.session_state.user_data.job_bytes = job_text.encode('utf-8')
                            
                            # Display results
                            st.subheader("Analysis Results")
                            
                            # Job title and company
                            st.markdown(f"**Position:** {job_data.get('title', 'Unknown')}")
                            st.markdown(f"**Company:** {job_data.get('company', 'Unknown')}")
                            
                            # Create columns for requirements
                            req_col1, req_col2 = st.columns(2)
                            
                            with req_col1:
                                st.markdown("**Required Skills:**")
                                for skill in job_data.get('required_skills', []):
                                    st.markdown(f"- {skill}")
                            
                            with req_col2:
                                st.markdown("**Preferred Skills:**")
                                for skill in job_data.get('preferred_skills', []):
                                    st.markdown(f"- {skill}")
                            
                            # Experience and education
                            st.markdown(f"**Experience:** {job_data.get('experience', 'Not specified')}")
                            st.markdown(f"**Education:** {job_data.get('education', 'Not specified')}")
                            
                            # Create the pathway option
                            if st.button("Create Career Pathway from This Job", key="create_pathway_btn"):
                                from job_postings_merged import convert_job_to_pathway
                                
                                pathway = convert_job_to_pathway(job_data)
                                st.session_state.user_data.selected_pathway = pathway['id']
                                
                                st.success(f"Created pathway: {pathway['name']}")
                                st.markdown("Go to the **AI Roadmap** tab to create a roadmap for this job.")
                            
                        except Exception as e:
                            st.error(f"Error analyzing job posting: {str(e)}")
                            st.session_state.job_data = None
                    else:
                        st.warning("Please enter a job description or URL.")
    
    with questionnaire_tab:
        st.subheader("Manual Questionnaire")
        st.write("If you don't have a resume or job posting, you can fill out this questionnaire instead.")
        
        # Skill assessment
        st.subheader("Your Skills")
        skill_text = st.text_area("List your top skills (separated by commas):", 
                                  placeholder="Python, project management, data analysis, communication...",
                                  key="skills_text")
        
        # Experience
        st.subheader("Your Experience")
        years_experience = st.slider("Years of professional experience:", 0, 30, 3, key="years_experience")
        
        experience_text = st.text_area("Briefly describe your most relevant experience:", 
                                      placeholder="I worked as a...",
                                      key="experience_text")
        
        # Education
        st.subheader("Your Education")
        education_level = st.selectbox("Highest level of education:", 
                                      ["High School", "Associate's", "Bachelor's", "Master's", "PhD", "Other"],
                                      key="education_level")
        
        education_field = st.text_input("Field of study:", key="education_field")
        
        # Career goals
        st.subheader("Your Career Goals")
        career_goal = st.text_area("What are your main career goals?", 
                                  placeholder="I want to become...",
                                  key="career_goal")
        
        # Save questionnaire data
        if st.button("Submit Questionnaire", key="submit_questionnaire"):
            # Process questionnaire data
            if skill_text:
                skills_list = [s.strip() for s in skill_text.split(",") if s.strip()]
                
                # Create a skills dictionary
                skills_dict = {}
                for skill in skills_list:
                    skills_dict[skill] = {"rating": 3, "experience": "Self-reported"}
                
                # Store in session state
                st.session_state.extracted_skills = skills_dict
                
                # Store other info in the user data
                questionnaire_data = {
                    "years_experience": years_experience,
                    "experience_description": experience_text,
                    "education_level": education_level,
                    "education_field": education_field,
                    "career_goal": career_goal,
                    "skills": skills_list
                }
                
                st.session_state.user_data.questionnaire = questionnaire_data
                
                st.success("Information saved successfully!")
                st.markdown("Go to the **Skill Graph** tab to visualize your skills and identify gaps.")
            else:
                st.warning("Please enter at least some skills.")

def render_skill_graph_tab():
    st.header("🧩 Skill Graph")
    skill_graph_page()

def main():
    # Initialize user data if not already in session state
    if "user_data" not in st.session_state:
        st.session_state.user_data = UserData()
    
    # Initialize active tab if not already set
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = 0
    
    # Main header
    st.markdown("""
        <div style='text-align: center'>
            <h1>CareerPath Navigator</h1>
            <h3>Find your path, build your skills, achieve your career goals</h3>
        </div>
    """, unsafe_allow_html=True)
    
    # Define tab names
    tab_names = [
        "Welcome",
        "Job & Resume Analysis",
        "AI Roadmap",
        "Skill Graph",
        "Project Portfolio",
        "2×2 Matrix",
        "Find Your Pathway",
        "About"
    ]
    
    # Create the tabs
    tabs = st.tabs(tab_names)
    
    # Set the active tab index (used by navigation buttons)
    tab_index = st.session_state.active_tab
    
    # Render the appropriate tab content based on active tab index
    with tabs[tab_index]:
        if tab_index == 0:
            render_welcome_tab()
        elif tab_index == 1:
            render_job_resume_tab()
        elif tab_index == 2:
            render_ai_roadmap_tab()
        elif tab_index == 3:
            render_skill_graph_tab()
        elif tab_index == 4:
            render_portfolio_tab()
        elif tab_index == 5:
            render_2x2_matrix_tab()
        elif tab_index == 6:
            render_find_pathway_tab()
        elif tab_index == 7:
            st.header("ℹ️ About")
            st.image(DEFAULT_IMAGES["data_viz_concept"], use_container_width=True)
            st.write("""
            CareerPath Navigator is built on Streamlit.  
            Use the tabs above to interact with every feature.  
            Your uploads & questionnaire answers persist as you move between pages.
            """)

if __name__ == "__main__":
    main()