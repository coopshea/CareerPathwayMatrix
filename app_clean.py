import streamlit as st
import pandas as pd
import json
import os
import random
import time
from datetime import datetime
from openai import OpenAI

from database import User, init_and_load_data, fetch_user_skills
from data import load_data, get_pathway_details, get_metrics_info
from visualizations import create_matrix_visualization
from recommendations import calculate_pathway_matches
from roadmaps import roadmap_generator_page
from ai_roadmap import ai_roadmap_generator_page
from job_postings import job_posting_page
from skills_analysis import skills_analysis_page
from skill_graph import skill_graph_page
from utils import create_pathway_card, DEFAULT_IMAGES
from streamlit_chat import message

# Initialize or get the database data
init_and_load_data()

# Load all data needed for the app
pathways_data, metrics_data, categories = load_data()

# Add a title and favicon for the app
st.set_page_config(
    page_title="CareerPath Navigator",
    page_icon="🧭",
    layout="wide"
)

# User Authentication System
class UserAuth:
    @staticmethod
    def initialize():
        """Initialize user authentication system"""
        if "authenticated" not in st.session_state:
            st.session_state.authenticated = False
            st.session_state.user_id = None
            st.session_state.user_name = None
            st.session_state.user_email = None
    
    @staticmethod
    def login_user_form():
        """Display login form and handle sign-in"""
        with st.form("login_form"):
            st.write("### Sign in to CareerPath Navigator")
            name = st.text_input("Full Name")
            email = st.text_input("Email")
            organization = st.text_input("Organization (optional)")
            
            submitted = st.form_submit_button("Sign In")
            
            if submitted and name and email:
                # Create a user ID from the email (MD5 hash)
                import hashlib
                user_id = hashlib.md5(email.encode()).hexdigest()
                
                # Set the session state
                st.session_state.authenticated = True
                st.session_state.user_id = user_id
                st.session_state.user_name = name
                st.session_state.user_email = email
                
                # Save user info to database
                user_info = {
                    "id": user_id,
                    "name": name,
                    "email": email,
                    "last_login": time.time()
                }
                UserAuth._save_user(user_info)
                
                # Rerun the app to show the authenticated view
                st.rerun()
            
            elif submitted:
                st.error("Please enter your name and email to sign in.")
    
    @staticmethod
    def display_user_info():
        """Display current user information and logout button"""
        with st.sidebar:
            st.write(f"Signed in as: **{st.session_state.user_name}**")
            if st.button("Sign Out"):
                UserAuth.logout()
                st.rerun()
    
    @staticmethod
    def get_current_user():
        """Get the current user information"""
        if UserAuth.is_authenticated():
            return {
                "id": st.session_state.user_id,
                "name": st.session_state.user_name,
                "email": st.session_state.user_email
            }
        return None
    
    @staticmethod
    def is_authenticated():
        """Check if a user is currently authenticated"""
        return st.session_state.get("authenticated", False)
    
    @staticmethod
    def logout():
        """Log out the current user"""
        st.session_state.authenticated = False
        st.session_state.user_id = None
        st.session_state.user_name = None
        st.session_state.user_email = None
        
        # Clear other session state variables
        for key in list(st.session_state.keys()):
            if key not in ["authenticated", "user_id", "user_name", "user_email"]:
                del st.session_state[key]
    
    @staticmethod
    def _save_user(user_info):
        """Save user information to persistent storage"""
        try:
            from database import User
            from sqlalchemy.orm import Session
            from sqlalchemy import create_engine
            
            # Connect to database
            engine = create_engine(os.environ["DATABASE_URL"])
            with Session(engine) as session:
                # Check if user already exists
                user = session.query(User).filter(User.id == user_info["id"]).first()
                
                if not user:
                    # Create new user
                    user = User(
                        id=user_info["id"],
                        name=user_info["name"],
                        email=user_info["email"],
                        last_login=user_info["last_login"]
                    )
                    session.add(user)
                else:
                    # Update existing user
                    user.last_login = user_info["last_login"]
                
                session.commit()
                
        except Exception as e:
            # If there's an error, log it but don't crash
            print(f"Error saving user: {e}")
            # You might also want to add a notification in the UI here

# Initialize authentication
UserAuth.initialize()

# Set up the main layout
if not UserAuth.is_authenticated():
    # Show login form if not authenticated
    UserAuth.login_user_form()
else:
    # Get user information
    user_info = UserAuth.get_current_user()
    user_id = user_info["id"]
    user_name = user_info["name"]
    user_email = user_info["email"]
    
    # Display user info in sidebar
    UserAuth.display_user_info()
    
    # Process user questions for AI chat assistant
    def process_user_question(question):
        """Process user questions and return appropriate responses with navigation guidance"""
        # Handle None case
        if question is None:
            return "I can help you explore different career paths and develop your skills. What would you like to know?"
            
        question_lower = question.lower()
        
        # Define keywords for different tabs
        tab_keywords = {
            1: ["matrix", "compare careers", "2x2", "visualization"],
            2: ["find pathway", "questionnaire", "preferences", "career match"],
            3: ["roadmap", "basic roadmap", "career steps"],
            4: ["ai roadmap", "personalized roadmap", "personal roadmap"],
            5: ["job posting", "analyze job", "job description", "job requirements"],
            6: ["skills analysis", "skill demand", "market skills"],
            7: ["skill graph", "skills visualization", "skill connections", "upload resume"]
        }
        
        # Check for quick responses based on keywords
        quick_responses = {
            "hello": f"Hello {user_name}! How can I help with your career planning today?",
            "hi": f"Hi {user_name}! What aspect of your career journey would you like to explore?",
            "what can you do": "I can help you explore career pathways, analyze skills, compare career options, and create personalized roadmaps based on your skills and preferences.",
            "how does this work": "CareerPath Navigator helps you discover optimal career paths by matching your preferences and skills to different career options. Use the Find Your Pathway tab to take a questionnaire, upload your resume in the Skill Graph tab, or analyze job postings in the Job Posting tab.",
            "thank": "You're welcome! Is there anything else I can help with regarding your career planning?",
            "bye": "Goodbye! Come back anytime for more career guidance and exploration."
        }
        
        for keyword, response in quick_responses.items():
            if keyword in question_lower:
                return response
        
        # Try to generate an AI response with OpenAI
        try:
            placeholder = st.empty()
            return stream_ai_response(question, placeholder)
        except Exception as e:
            # Fall back to rule-based navigation guidance
            for tab_idx, keywords in tab_keywords.items():
                for keyword in keywords:
                    if keyword in question_lower:
                        st.session_state.active_tab = tab_idx
                        return f"I can help you with that. I'll navigate to the relevant section: {keyword}. Is there anything specific you'd like to know about it?"
            
            # If no keyword matched, provide a general response
            return "I can help you explore career paths, analyze skills, and create personalized roadmaps. For the best experience, try filling out the questionnaire in the 'Find Your Pathway' tab or uploading your resume in the 'Skill Graph' tab. What would you like to do today?"
    
    # Stream AI-powered response with word-by-word display
    def stream_ai_response(question, placeholder):
        """Generate and stream an AI-powered response using OpenAI API"""
        # Handle None case
        if question is None:
            return "I can help you explore different career paths and develop your skills. What would you like to know?"
            
        try:
            # Get the API key from environment variable
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                return "I couldn't access the OpenAI API key. Using rule-based responses instead.\n\n" + get_quick_response(question)
            
            # Create OpenAI client
            client = OpenAI(api_key=api_key)
            
            # Generate response with context about the application
            response = client.chat.completions.create(
                model="gpt-4o",  # Use the latest model
                messages=[
                    {"role": "system", "content": """You are a helpful career assistant in the CareerPath Navigator application. 
                    You should encourage users to:
                    1. Fill out the career preferences questionnaire in the 'Find Your Pathway' tab
                    2. Upload their resume in the 'Skill Graph' tab for skill analysis
                    3. Return to chat for personalized guidance based on their profile
                    
                    You can guide users to different features:
                    - 2x2 Matrix (tab 1): For comparing career paths visually
                    - Find Your Pathway (tab 2): For matching preferences to careers
                    - Basic Roadmap (tab 3): For generating simple career roadmaps
                    - AI Roadmap (tab 4): For generating AI-powered personalized roadmaps
                    - Job Posting (tab 5): For analyzing job opportunities
                    - Skills Analysis (tab 6): For finding high-impact skills in the market
                    - Skill Graph (tab 7): For analyzing user skills and gaps
                    
                    Keep responses friendly, concise and helpful. Always recommend the appropriate tool
                    based on what the user is trying to accomplish."""},
                    {"role": "user", "content": question}
                ],
                stream=True
            )
            
            # For displaying the response word by word
            collected_content = ""
            for chunk in response:
                content = chunk.choices[0].delta.content
                if content:
                    collected_content += content
                    placeholder.markdown(collected_content)
            
            # Check for keywords to navigate to tabs
            question_lower = question.lower()
            collected_content_lower = collected_content.lower()
            
            tab_keywords = {
                1: ["matrix", "compare careers", "2x2", "visualization"],
                2: ["find pathway", "questionnaire", "preferences", "career match"],
                3: ["roadmap", "basic roadmap", "career steps"],
                4: ["ai roadmap", "personalized roadmap", "personal roadmap"],
                5: ["job posting", "analyze job", "job description", "job requirements"],
                6: ["skills analysis", "skill demand", "market skills"],
                7: ["skill graph", "skills visualization", "skill connections", "upload resume"]
            }
            
            # Check if the response suggests navigating to a specific tab
            for tab_idx, keywords in tab_keywords.items():
                for keyword in keywords:
                    if keyword in response_lower:
                        st.session_state.active_tab = tab_idx
                        break
                
            return collected_content
            
        except Exception as e:
            # Fall back to rule-based response
            fallback = f"I encountered an error with the AI response. Using rule-based responses instead.\n\n" + get_quick_response(question)
            placeholder.markdown(fallback)
            return fallback
    
    # Get AI-powered response using OpenAI (non-streaming version)
    def get_ai_response(question):
        """Generate an AI-powered response using OpenAI API (for backward compatibility)"""
        # Handle None case
        if question is None:
            return "I can help you explore different career paths and develop your skills. What would you like to know?"
            
        try:
            # Get the API key from environment variable
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                return "I couldn't access the OpenAI API key. Using rule-based responses instead.\n\n" + get_quick_response(question)
            
            from openai import OpenAI
            
            # Create OpenAI client
            client = OpenAI(api_key=api_key)
            
            # Generate response with context about the application
            ai_response = client.chat.completions.create(
                model="gpt-4o",  # Use the latest model
                messages=[
                    {"role": "system", "content": """You are a helpful career assistant in the CareerPath Navigator application. 
                    You should encourage users to:
                    1. Fill out the career preferences questionnaire in the 'Find Your Pathway' tab
                    2. Upload their resume in the 'Skill Graph' tab for skill analysis
                    3. Return to chat for personalized guidance based on their profile
                    
                    You can guide users to different features:
                    - 2x2 Matrix (tab 1): For comparing career paths visually
                    - Find Your Pathway (tab 2): For matching preferences to careers
                    - Basic Roadmap (tab 3): For generating simple career roadmaps
                    - AI Roadmap (tab 4): For generating AI-powered personalized roadmaps
                    - Job Posting (tab 5): For analyzing job opportunities
                    - Skills Analysis (tab 6): For finding high-impact skills in the market
                    - Skill Graph (tab 7): For analyzing user skills and gaps
                    
                    Keep responses friendly, concise and helpful. Always recommend the appropriate tool
                    based on what the user is trying to accomplish."""},
                    {"role": "user", "content": question}
                ]
            )
            
            return ai_response.choices[0].message.content
            
        except Exception as e:
            # Return the error message and fall back to a quick response
            return f"Error generating AI response: {str(e)}\n\nFalling back to rule-based response:\n" + get_quick_response(question)
    
    # Get a quick response based on keywords (fallback option)
    def get_quick_response(question):
        """Provide quick responses based on keywords for low latency"""
        question_lower = question.lower()
        
        # Define responses based on keywords
        keyword_responses = {
            "compare": "You can compare different career paths using our 2x2 Matrix visualization in the second tab. It allows you to see how different careers rank on various metrics like skill match and growth potential.",
            "pathways": "The 'Find Your Pathway' tab helps you discover career paths that match your preferences. Just fill out the questionnaire to see personalized recommendations.",
            "roadmap": "We offer two types of roadmaps - a basic roadmap in tab 4 and an AI-powered personalized roadmap in tab 5. The AI roadmap integrates data from your resume and questionnaire for more tailored guidance.",
            "resume": "You can upload your resume in the 'Skill Graph' tab to visualize your skills and see how they connect to potential career opportunities.",
            "jobs": "The 'Job Posting' tab allows you to analyze job descriptions to understand their requirements and identify skill gaps you might need to fill.",
            "skills": "We offer several tools for skills analysis. The 'Skills Analysis' tab shows high-demand skills in the job market, while the 'Skill Graph' visualizes your personal skills network.",
            "matrix": "Our 2x2 Matrix visualization in the second tab helps you compare different career paths based on key metrics like skill match and growth potential."
        }
        
        # Check for keyword matches
        for keyword, response in keyword_responses.items():
            if keyword in question_lower:
                return response
        
        # Default response if no keywords match
        return "I can help you explore career paths, analyze skills, and create personalized roadmaps. For the best experience, try filling out the questionnaire in the 'Find Your Pathway' tab or uploading your resume in the 'Skill Graph' tab. What would you like to do today?"
    
    # AI Chat Assistant Helper for the welcome page
    def ai_chat_assistant():
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
        
        # Display chat messages from history on app rerun
        if 'messages' in st.session_state:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
        else:
            st.session_state.messages = []
        
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
                            
                            # In a full implementation, save all responses to database
                            from database import ChatMessage
                            # Logic to save to database would go here
                            
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
    
    # Create tabs
    tab_names = [
        "Welcome", "2x2 Matrix", "Find Your Pathway", "Basic Roadmap", "AI Roadmap", 
        "Job Posting", "Skills Analysis", "Skill Graph", "About"
    ]
    
    # Initialize active tab if not already set
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = 0
    
    # Create the tabs at the top of the page
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs(tab_names)
    
    # Welcome tab content
    with tab1:
        # Button grid - 3x2 layout
        st.write("")  # Add some space at the top
        
        # Create two columns in each row for a 2x3 grid
        for row in range(3):
            col1, col2 = st.columns(2)
            
            # First column in this row
            with col1:
                if row == 0:
                    # First button - Explore Career Paths
                    st.write("### 🧭 Explore Career Paths")
                    st.write("Discover recommended career pathways based on your preferences and skills.")
                    if st.button("Find Your Pathway", key=f"btn_{row}_1"):
                        st.session_state.active_tab = 2  # Navigate to Find Your Pathway tab
                        st.rerun()
                elif row == 1:
                    # Third button - Skills Graph
                    st.write("### 🌐 Skills Graph")
                    st.write("Visualize your skills and see how they connect to potential career opportunities.")
                    if st.button("View Skill Graph", key=f"btn_{row}_1"):
                        st.session_state.active_tab = 7  # Navigate to Skill Graph tab
                        st.rerun()
                else:  # row == 2
                    # Fifth button - AI Chat
                    st.write("### 💬 AI Career Assistant")
                    st.write("Chat with our AI assistant for personalized career guidance and advice.")
                    if st.button("Open AI Chat", key=f"btn_{row}_1"):
                        # Just scroll to the chat widget which is in the sidebar
                        st.write("AI Chat is available in the sidebar!")
            
            # Second column in this row
            with col2:
                if row == 0:
                    # Second button - Career Matrix
                    st.write("### 📊 Career Matrix")
                    st.write("Compare different career options on a visual 2x2 matrix based on key metrics.")
                    if st.button("View Matrix", key=f"btn_{row}_2"):
                        st.session_state.active_tab = 1  # Navigate to 2x2 Matrix tab
                        st.rerun()
                elif row == 1:
                    # Fourth button - Job Analysis
                    st.write("### 📋 Job Analysis")
                    st.write("Analyze job postings to understand requirements and identify skill gaps.")
                    if st.button("Analyze Jobs", key=f"btn_{row}_2"):
                        st.session_state.active_tab = 5  # Navigate to Job Posting tab
                        st.rerun()
                else:  # row == 2
                    # Sixth button - AI Roadmap
                    st.write("### 🗺️ AI Roadmap")
                    st.write("Generate a personalized AI roadmap for your career journey.")
                    if st.button("Generate Roadmap", key=f"btn_{row}_2"):
                        st.session_state.active_tab = 4  # Navigate to AI Roadmap tab
                        st.rerun()
        
        # Introduction text at the bottom
        st.write("## Welcome to CareerPath Navigator")
        st.write("""
        CareerPath Navigator is your AI-powered career development platform. We help you explore career options,
        identify skill gaps, and create personalized roadmaps to achieve your professional goals.
        
        To get started, explore the features above or navigate using the tabs at the top of the page.
        """)
        
        # Display random inspirational quote
        quotes = [
            ""Choose a job you love, and you will never have to work a day in your life." — Confucius",
            ""The future depends on what you do today." — Mahatma Gandhi",
            ""Success is not final, failure is not fatal: It is the courage to continue that counts." — Winston Churchill",
            ""The only way to do great work is to love what you do." — Steve Jobs",
            ""Believe you can and you're halfway there." — Theodore Roosevelt",
            ""The best way to predict your future is to create it." — Abraham Lincoln"
        ]
        
        st.markdown("---")
        st.markdown(f"***{random.choice(quotes)}***")
        
        # Add AI chat assistant to the sidebar
        with st.sidebar:
            # Initialize chat messages if not already in session state
            if "messages" not in st.session_state:
                greeting_name = f" {user_name}" if user_name else ""
                st.session_state.messages = [
                    {"role": "assistant", "content": f"Hello{greeting_name}! I'm your AI career assistant. To get the most out of CareerPath Navigator, I recommend:\n\n1. Fill out the career preferences questionnaire in the 'Find Your Pathway' tab\n2. Upload your resume in the 'Skill Graph' tab for skill analysis\n3. Return here for personalized career guidance based on your profile\n\nHow can I help you today?"}
                ]
            
            # Display the AI chat assistant
            ai_chat_assistant()
    
    # 2x2 Matrix tab content
    with tab2:
        # Create the matrix visualization
        create_matrix_visualization(pathways_data)
    
    # Find Your Pathway tab content
    with tab3:
        # Create the pathway recommendation content
        st.title("Find Your Pathway")
        st.write("""
        Complete the questionnaire below to discover career pathways that align with your preferences.
        """)
        
        # Create the questionnaire
        st.header("Career Preferences Questionnaire")
        
        metrics = metrics_data.keys()
        user_preferences = {}
        importance_weights = {}
        
        for metric_id in metrics:
            metric_info = metrics_data[metric_id]
            
            st.write(f"### {metric_info['name']}")
            st.write(metric_info['description'])
            
            # Ask for preference within a range
            preference_range = st.slider(
                f"Where do you prefer to be on the {metric_info['name']} scale?",
                0, 100, (30, 70),
                key=f"pref_{metric_id}"
            )
            
            # Ask for importance
            importance = st.slider(
                f"How important is {metric_info['name']} to you?",
                0, 10, 5,
                key=f"imp_{metric_id}"
            )
            
            user_preferences[metric_id] = preference_range
            importance_weights[metric_id] = importance
        
        # Button to calculate matches
        if st.button("Find Matching Pathways"):
            # Calculate matches
            matches = calculate_pathway_matches(pathways_data, user_preferences, importance_weights)
            
            # Display matches
            st.write("## Your Top Pathway Matches")
            
            # Display top 3 matches
            for i, (pathway_id, score, explanation) in enumerate(matches[:3]):
                pathway = get_pathway_details(pathways_data, pathway_id)
                
                st.write(f"### {i+1}. {pathway['name']} ({score:.1f}% match)")
                st.write(pathway['description'])
                
                with st.expander("Why this pathway matches your preferences"):
                    st.write(explanation)
                
                # Button to view detailed pathway
                if st.button(f"View Detailed Pathway", key=f"view_{i}"):
                    st.session_state.selected_pathway_id = pathway_id
                    st.session_state.active_tab = 1  # 2x2 Matrix tab
                    st.rerun()
                
                st.write("---")
            
            # Display remaining matches in a table
            if len(matches) > 3:
                st.write("### Other Potential Matches")
                
                # Prepare data for the table
                matches_data = []
                for pathway_id, score, _ in matches[3:10]:  # Show up to 10 total
                    pathway = get_pathway_details(pathways_data, pathway_id)
                    matches_data.append({
                        "Pathway": pathway['name'],
                        "Match Score": f"{score:.1f}%",
                        "Category": pathway['category']
                    })
                
                # Display as a table
                st.table(pd.DataFrame(matches_data))
    
    # Basic Roadmap tab
    with tab4:
        # Check if we're coming from a pathway detail view with a pre-selected pathway
        pre_selected_pathway = None
        if 'generate_roadmap_for' in st.session_state:
            pre_selected_pathway = st.session_state.generate_roadmap_for
            # Clear the session state so it doesn't persist
            del st.session_state.generate_roadmap_for
        
        roadmap_generator_page(pre_selected_pathway, pathways_data, metrics_data)
    
    # AI Roadmap tab
    with tab5:
        # Check if we're coming from a pathway detail view with a pre-selected pathway
        pre_selected_pathway = None
        if 'generate_roadmap_for' in st.session_state:
            pre_selected_pathway = st.session_state.generate_roadmap_for
            # Clear the session state so it doesn't persist
            del st.session_state.generate_roadmap_for
            
        ai_roadmap_generator_page(pre_selected_pathway, pathways_data, metrics_data)
    
    # Job Posting tab
    with tab6:
        job_posting_page(pathways_data, metrics_data)
    
    # Skills Analysis tab
    with tab7:
        skills_analysis_page()
    
    # Skill Graph tab
    with tab8:
        skill_graph_page()
    
    # About tab
    with tab9:
        # About page content
        st.image(DEFAULT_IMAGES["data_viz_concept"], use_container_width=True)
        
        st.write("## About CareerPath Navigator")
        
        st.write("""CareerPath Navigator is a comprehensive career development platform that leverages AI 
    to transform skill management, career planning, and professional growth through intelligent, 
    data-driven insights.
    """)
        
        st.write("### Key Features")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("#### AI-Powered Career Guidance")
            st.write("""Our platform uses advanced AI to provide personalized career guidance based 
            on your skills, preferences, and goals. The AI assistant can answer questions, suggest 
            career paths, and provide tailored advice for your unique journey.""")
            
            st.write("#### Interactive Skills Visualization")
            st.write("""Visualize your skills as an interactive network to understand relationships
            between different abilities and how they connect to potential career paths. Identify
            skill gaps and plan your learning journey.""")
        
        with col2:
            st.write("#### Career Pathway Exploration")
            st.write("""Discover and compare different career pathways based on your preferences
            using our 2x2 matrix visualization. Find paths that align with your values, skills,
            and goals.""")
            
            st.write("#### Personalized Roadmaps")
            st.write("""Generate custom roadmaps that outline the steps needed to reach your 
            career goals. Our AI creates detailed action plans tailored to your unique situation
            and professional aspirations.""")
        
        st.write("### About the Team")
        st.write("""CareerPath Navigator was created by a team of career development experts,
        data scientists, and software engineers passionate about helping people navigate their
        professional journeys with confidence and clarity.""")
        
        st.write("### Contact")
        st.write("""For questions, feedback, or support, please contact us at:
        team@careerpathnavigator.com""")