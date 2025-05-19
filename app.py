import streamlit as st
import pandas as pd
import numpy as np
import time
import os
import json
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
from user_auth import UserAuth
from database import Session, User, ChatMessage, UserDocument

# Configure page
st.set_page_config(
    page_title="CareerPath Navigator",
    page_icon="🧭",
    layout="wide"
)

# Load the data
pathways_data, metrics_data, categories = load_data()

# Main header
st.markdown("""
    <div style='text-align: center'>
        <h1>CareerPath Navigator</h1>
        <h3>Find your path, build your skills, achieve your career goals</h3>
    </div>
""", unsafe_allow_html=True)

# Initialize session state variables
if "user" not in st.session_state:
    st.session_state.user = None

# MANDATORY LOGIN CHECK
# If user is not logged in, show only the login form and nothing else
if st.session_state.user is None:
    st.markdown("### Sign in to access CareerPath Navigator")
    st.markdown("Please enter your information to proceed. This helps us understand who is using the application.")
    
    # Create two columns for the form and info
    login_col1, login_col2 = st.columns([3, 2])
    
    with login_col1:
        # Create the sign-in form
        with st.form("login_form", clear_on_submit=False):
            full_name = st.text_input("Full Name", key="name_input", placeholder="Your full name")
            email = st.text_input("Email", key="email_input", placeholder="your.email@example.com")
            organization = st.text_input("Organization (Optional)", key="org_input", placeholder="Company or school name")
            
            submitted = st.form_submit_button("Sign In")
            
            if submitted:
                # Simple validation
                if not full_name or not email or "@" not in email:
                    st.error("Please enter a valid name and email address to continue.")
                else:
                    # Create a simple hash for the user identifier
                    import hashlib
                    user_id = hashlib.md5(email.encode()).hexdigest()
                    
                    # Store user information
                    user_info = {
                        "id": user_id,
                        "name": full_name,
                        "email": email,
                        "organization": organization,
                        "created_at": time.time(),
                        "last_login": time.time()
                    }
                    
                    # Save to session state
                    st.session_state.user = user_info
                    
                    # Save to database (to be implemented in the future)
                    try:
                        session = Session()
                        db_user = session.query(User).filter(User.id == user_id).first()
                        if db_user:
                            # Update existing user
                            db_user.name = full_name
                            db_user.email = email
                            db_user.last_login = float(time.time())
                        else:
                            # Create new user
                            db_user = User(
                                id=user_id,
                                name=full_name,
                                email=email,
                                created_at=float(time.time()),
                                last_login=float(time.time())
                            )
                            session.add(db_user)
                        session.commit()
                        session.close()
                    except Exception as e:
                        print(f"Error saving user to database: {e}")
                    
                    st.success(f"Welcome, {full_name}!")
                    st.rerun()
    
    with login_col2:
        st.markdown("""
        ### Why Sign In?
        
        Your information helps us:
        
        - Track who is using the platform
        - Contact you about updates and features
        - Save your career preferences
        - Provide personalized recommendations
        - Remember your uploads and chat history
        
        We respect your privacy and do not share your data with third parties.
        """)
    
    # Stop execution here to force login
    st.stop()

# If we get here, the user is logged in
# Show small user info and logout in the corner
auth_col1, auth_col2 = st.columns([3, 1])
with auth_col2:
    st.write(f"**Signed in as:** {st.session_state.user['name']}")
    if st.button("Sign Out", key="nav_signout_btn"):
        st.session_state.user = None
        st.rerun()

# Initialize chat messages if not already in session state
if "messages" not in st.session_state:
    # Check if user is logged in to personalize greeting
    greeting_name = f", {st.session_state.user['name'].split()[0]}" if st.session_state.user else ""
    st.session_state.messages = [
        {"role": "assistant", "content": f"Hello{greeting_name}! I'm your AI career assistant. To get the most out of CareerPath Navigator, I recommend:\n\n1. Fill out the career preferences questionnaire in the 'Find Your Pathway' tab\n2. Upload your resume in the 'Skill Graph' tab for skill analysis\n3. Return here for personalized career guidance based on your profile\n\nHow can I help you today?"}
    ]

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
    
    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Accept user input
    if prompt := st.chat_input("Ask me about career paths, skills, or job opportunities..."):
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
        
        # Create a placeholder for the assistant's response
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            
            # Stream the response from API
            full_response = stream_ai_response(prompt, response_placeholder)
            
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": full_response})

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
            fallback = "I couldn't access the OpenAI API key. Using rule-based responses instead.\n\n" + get_quick_response(question)
            placeholder.markdown(fallback)
            return fallback
        
        from openai import OpenAI
        
        # Create OpenAI client
        client = OpenAI(api_key=api_key)
        
        # System message for the chat context
        system_message = """You are a helpful career assistant in the CareerPath Navigator application. 
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
        based on what the user is trying to accomplish."""
        
        # Generate streaming response with context about the application
        stream = client.chat.completions.create(
            model="gpt-4o",  # Use the latest model
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": question}
            ],
            max_tokens=250,
            stream=True
        )
        
        # Process the streaming response
        collected_chunks = []
        collected_content = ""
        
        # Display the streaming response in real-time
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                content_piece = chunk.choices[0].delta.content
                collected_chunks.append(content_piece)
                collected_content += content_piece
                placeholder.markdown(collected_content + "▌")
        
        # Display the final response without cursor
        placeholder.markdown(collected_content)
        
        # Extract any tab guidance from the AI response
        tab_keywords = {
            "2x2 matrix": 1,
            "career matrix": 1, 
            "find your pathway": 2,
            "matching": 2,
            "preferences": 2,
            "basic roadmap": 3,
            "ai roadmap": 4,
            "roadmap generator": 4,
            "job posting": 5,
            "analyze job": 5,
            "skills analysis": 6,
            "high-impact skills": 6,
            "skill graph": 7,
            "skill gaps": 7
        }
        
        # Check if any keywords appear in the response
        if collected_content and isinstance(collected_content, str):
            response_lower = collected_content.lower()
            for keyword, tab_idx in tab_keywords.items():
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
            ],
            max_tokens=250
        )
        
        # Get the response content
        response = ai_response.choices[0].message.content
        
        # Extract any tab guidance from the AI response
        tab_keywords = {
            "2x2 matrix": 1,
            "career matrix": 1, 
            "find your pathway": 2,
            "matching": 2,
            "preferences": 2,
            "basic roadmap": 3,
            "ai roadmap": 4,
            "roadmap generator": 4,
            "job posting": 5,
            "analyze job": 5,
            "skills analysis": 6,
            "high-impact skills": 6,
            "skill graph": 7,
            "skill gaps": 7
        }
        
        # Check if any keywords appear in the response
        if response is not None and isinstance(response, str):
            response_lower = response.lower()
            for keyword, tab_idx in tab_keywords.items():
                if keyword in response_lower:
                    st.session_state.active_tab = tab_idx
                    break
                
        return response
        
    except Exception as e:
        # Fall back to rule-based response
        return f"I encountered an error with the AI response. Using rule-based responses instead.\n\n" + get_quick_response(question)

# Provide quick rule-based responses based on keywords for low latency
def get_quick_response(question):
    """Provide quick responses based on keywords for low latency"""
    # Default to empty string if question is None
    if question is None:
        return "I can help you explore different career paths and develop your skills. What would you like to know?"
        
    question = question.lower()
    
    # Career guidance prompt responses
    if "resume" in question and ("upload" in question or "analyze" in question):
        st.session_state.active_tab = 7  # Skill Graph tab
        return "I recommend uploading your resume in the Skill Graph tab. This will help us analyze your skills and identify gaps. I've selected that tab for you!"
        
    if "questionnaire" in question or "preferences" in question:
        st.session_state.active_tab = 2  # Find Your Pathway tab
        return "To find career paths that match your preferences, please fill out the questionnaire in the Find Your Pathway tab. I've selected that tab for you!"
        
    if "personalized" in question or "custom" in question or "for me" in question:
        return "For truly personalized guidance, I recommend:\n\n1. Complete the questionnaire in the 'Find Your Pathway' tab\n2. Upload your resume in the 'Skill Graph' tab\n\nOnce you've done both, I can provide much more tailored advice!"
    
    # Simple mapping of keywords to responses and tab navigation
    response_map = {
        "compare": (1, "I'll show you the Career Matrix to compare different paths."),
        "career path": (1, "Let's explore career paths in the 2x2 Matrix."),
        "explore": (1, "The Career Matrix is perfect for exploration."),
        "matrix": (1, "Opening the 2x2 Matrix visualization for you."),
        
        "skill": (7, "Let's check out your skills in the Skill Graph."),
        "gap": (7, "The Skill Graph will help identify your skill gaps."),
        "analyze": (7, "I'll help you analyze your skills with our Skill Graph."),
        
        "job": (5, "Let's analyze a job posting for you."),
        "posting": (5, "The Job Posting analyzer will help evaluate opportunities."),
        "opportunity": (5, "I'll open the Job Posting analyzer for you."),
        
        "roadmap": (4, "Let's create a career roadmap for you."),
        "plan": (4, "The AI Roadmap generator will help you plan your career."),
        "develop": (4, "Let's develop your career plan with the AI Roadmap."),
        
        "recommend": (2, "Let's find pathways that match your preferences."),
        "match": (2, "The Pathway Finder will help match you with careers."),
        
        "market": (6, "Let's analyze market trends in Skills Analysis."),
        "demand": (6, "The Skills Analysis tool shows high-demand skills."),
        "high impact": (6, "I'll show you high-impact skills in the market.")
    }
    
    # Check for keyword matches
    for keyword, (tab_index, response) in response_map.items():
        if keyword in question:
            st.session_state.active_tab = tab_index
            return response
    
    # Default response if no match
    return "I can help you explore career paths, analyze skills, and create personalized roadmaps. For the best experience, I recommend filling out the questionnaire in the 'Find Your Pathway' tab and uploading your resume in the 'Skill Graph' tab. What would you like to do today?"

# Create tabs
tab_names = [
    "Welcome", "2x2 Matrix", "Find Your Pathway", "Basic Roadmap", "AI Roadmap", 
    "Job Posting", "Skills Analysis", "Skill Graph", "About"
]

# Initialize active tab if not already set
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = 0

# Create the tabs at the top of the page - there are 9 tabs total
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs(tab_names)

# Welcome tab content
with tab1:
    # Button grid - 3x2 layout
    st.write("")  # Add some space at the top
    
    # Create 3 rows of 2 buttons each
    row1 = st.columns(2)
    with row1[0]:
        if st.button("📊 Compare Career Paths", use_container_width=True, key="btn_matrix"):
            st.session_state.active_tab = 1  # 2x2 Matrix tab
            st.rerun()
    
    with row1[1]:
        if st.button("💡 Find Matching Careers", use_container_width=True, key="btn_pathway"):
            st.session_state.active_tab = 2  # Find Your Pathway tab
            st.rerun()
    
    row2 = st.columns(2)
    with row2[0]:
        if st.button("🧩 Analyze My Skills", use_container_width=True, key="btn_skills"):
            st.session_state.active_tab = 7  # Skill Graph tab
            st.rerun()
    
    with row2[1]:
        if st.button("🛣️ Create Career Roadmap", use_container_width=True, key="btn_roadmap"):
            st.session_state.active_tab = 4  # AI Roadmap tab
            st.rerun()
    
    row3 = st.columns(2)
    with row3[0]:
        if st.button("🔍 Analyze Job Posting", use_container_width=True, key="btn_job"):
            st.session_state.active_tab = 5  # Job Posting tab
            st.rerun()
    
    with row3[1]:
        if st.button("📈 Find High-Impact Skills", use_container_width=True, key="btn_market"):
            st.session_state.active_tab = 6  # Skills Analysis tab
            st.rerun()
        
        # AI chat assistant below the buttons
        st.markdown("---")
        st.markdown("### Not sure where to start?")
        
        # AI chat assistant
        ai_chat_assistant()

# 2x2 Matrix tab
with tab2:
        st.write("## Find Your Ideal Career Path")
        st.write("""
        Visualize career options based on how well they match your skills and interests. The 2x2 matrix helps you identify
        paths that align with your strengths and passions, making career decisions easier and more fulfilling.
        """)
        
        # Only show sidebar in this tab
        with st.sidebar:
            st.markdown("## Matrix Controls")
            
            # Category filters - add key parameter to fix duplicate element issue
            selected_categories = st.multiselect(
                "Filter by Category",
                ["All"] + categories,
                default=["All"],
                key="matrix_categories"
            )
            
            if "All" in selected_categories:
                filtered_pathways = pathways_data
            else:
                filtered_pathways = pathways_data[pathways_data['category'].isin(selected_categories)]
            
            # Select x and y axis metrics with defaults focused on skills and enjoyment
            x_metric = st.selectbox(
                "X-Axis Metric", 
                list(metrics_data.keys()),
                index=list(metrics_data.keys()).index("skill_match") if "skill_match" in metrics_data else 0,
                key="x_axis_metric"
            )
            
            y_metric = st.selectbox(
                "Y-Axis Metric", 
                list(metrics_data.keys()),
                index=list(metrics_data.keys()).index("enjoyment_factor") if "enjoyment_factor" in metrics_data else 0,
                key="y_axis_metric"
            )
            
            # Additional info for selected metrics
            st.markdown(f"### {metrics_data[x_metric]['name']}")
            st.write(metrics_data[x_metric]['description'])
            st.markdown(f"### {metrics_data[y_metric]['name']}")
            st.write(metrics_data[y_metric]['description'])
        
        # Create the matrix visualization
        figure = create_matrix_visualization(filtered_pathways, x_metric, y_metric, metrics_data)
        st.plotly_chart(figure, use_container_width=True)
        
        # Display selected pathway details
        st.write("## Pathway Details")
        if 'selected_pathway' not in st.session_state:
            st.session_state.selected_pathway = None
        
        # Instructions if no pathway is selected
        if st.session_state.selected_pathway is None:
            st.info("👆 Click on a pathway in the matrix above to see detailed information")
        else:
            # Get details for the selected pathway
            pathway_details = get_pathway_details(pathways_data, st.session_state.selected_pathway)
            
            # Create columns for the pathway details
            col1, col2 = st.columns([2, 3])
            
            with col1:
                st.write(f"### {pathway_details['name']}")
                st.write(f"**Category:** {pathway_details['category']}")
                st.write(f"**Description:** {pathway_details['description']}")
                st.write("**Target Customers:** " + pathway_details['target_customers'])
                st.write("**Success Examples:** " + ", ".join(pathway_details['success_examples']))
                st.write("**Key Skills:**")
                for skill in pathway_details['key_skills']:
                    st.markdown(f"- {skill}")
            
            with col2:
                # Create expandable sections for pathway details
                with st.expander("Key Metrics", expanded=True):
                    # Show key metrics in a clean table format
                    key_metrics = ["risk_level", "success_probability", "terminal_value", "expected_value_10yr"]
                    key_data = []
                    
                    for metric in key_metrics:
                        if metric in pathway_details['metrics']:
                            metric_info = pathway_details['metrics'][metric]
                            key_data.append({
                                "Metric": metrics_data[metric]['name'],
                                "Value": f"{metric_info['value']}/10",
                                "Interpretation": metrics_data[metric]['rubric'][str(metric_info['value'])]
                            })
                    
                    st.table(pd.DataFrame(key_data))
                    
                with st.expander("All Metrics", expanded=False):
                    # Show all metrics in a table format
                    all_data = []
                    for metric_key, metric_info in pathway_details['metrics'].items():
                        all_data.append({
                            "Metric": metrics_data[metric_key]['name'],
                            "Value": f"{metric_info['value']}/10",
                            "Interpretation": metrics_data[metric_key]['rubric'][str(metric_info['value'])]
                        })
                    
                    st.table(pd.DataFrame(all_data))
                    
                with st.expander("Sources & Evidence", expanded=False):
                    selected_metric = st.selectbox(
                        "Select metric to view sources",
                        list(pathway_details['metrics'].keys()),
                        format_func=lambda x: metrics_data[x]['name'],
                        key="source_metric"
                    )
                    
                    if 'sources' in pathway_details['metrics'][selected_metric]:
                        for source in pathway_details['metrics'][selected_metric]['sources']:
                            st.write(f"**{source['title']}** - {source['publisher']}")
                            st.write(f"> {source['extract']}")
                            st.write(f"[Read more]({source['url']})")
                    else:
                        st.write("No sources available for this metric.")
                    
                with st.expander("Rationale", expanded=False):
                    if 'rationale' in pathway_details:
                        for metric, explanation in pathway_details['rationale'].items():
                            st.write(f"**{metrics_data[metric]['name']}:** {explanation}")
                    else:
                        st.write("No detailed rationale available for this pathway.")
                
                # Add buttons to generate roadmaps for this pathway
                roadmap_cols = st.columns(2)
                with roadmap_cols[0]:
                    if st.button("Generate Basic Roadmap", key="gen_basic"):
                        # Set a session state variable to indicate we want to switch to the basic roadmap tab
                        # with this pathway pre-selected
                        st.session_state.generate_roadmap_for = pathway_details
                        # Switch to the basic roadmap tab (index 3)
                        st.session_state.active_tab = 3
                        st.rerun()
                with roadmap_cols[1]:
                    if st.button("Generate AI-Powered Roadmap", key="gen_ai"):
                        # Set a session state variable to indicate we want to switch to the AI roadmap tab
                        # with this pathway pre-selected
                        st.session_state.generate_roadmap_for = pathway_details
                        # Switch to the AI roadmap tab (index 4)
                        st.session_state.active_tab = 4
                        st.rerun()

# Find Your Pathway tab
with tab3:
        st.write("## Find Pathways That Match Your Preferences")
        st.write("""
        Use the sliders below to indicate your preferences for different aspects of a career pathway. 
        The tool will calculate how well each pathway matches your preferences and show the best matches.
        """)
        
        # First show reflective questions to help users think about their preferences
        with st.expander("Reflective Questions to Consider", expanded=False):
            questions = [
                {
                    "topic": "Risk Tolerance",
                    "question": "Think about past career decisions. How did you feel when taking risks versus pursuing safer options? Did you feel more energized by stability or by potential upside?",
                    "relevance": "Understanding your personal risk tolerance helps identify pathways that match your comfort level."
                },
                {
                    "topic": "Technical Specialization",
                    "question": "Consider times when you've deeply specialized versus remained a generalist. Which approach felt more natural to you?",
                    "relevance": "Some pathways require deep technical expertise while others reward breadth of knowledge."
                },
                {
                    "topic": "Time Horizon",
                    "question": "Reflect on your patience with delayed gratification. Are you willing to invest years before seeing significant returns?",
                    "relevance": "Pathways differ dramatically in how quickly they deliver financial returns."
                },
                {
                    "topic": "Control vs. Optionality",
                    "question": "Consider situations where you had to choose between maintaining full control and preserving future options. Which did you prioritize?",
                    "relevance": "Certain paths offer greater autonomy while others maintain flexibility to pivot."
                },
                {
                    "topic": "Network Reliance",
                    "question": "How comfortable are you with success depending on your ability to build and leverage professional relationships?",
                    "relevance": "Pathways vary significantly in their dependency on networks and connections."
                }
            ]
            
            for q_idx, q in enumerate(questions):
                st.write(f"**{q['topic']}**")
                st.write(q['question'])
                st.write(f"*{q['relevance']}*")
                st.write("---")
        
        # Create columns for preference input
        col1, col2 = st.columns(2)
        
        # Dictionary to store user preferences
        user_preferences = {}
        importance_weights = {}
        
        # Select which metrics to show in the preference input
        preference_metrics = ["risk_level", "capital_requirements", "technical_specialization", 
                             "network_dependency", "time_to_return", "control", "optionality"]
        
        # Create preference sliders in two columns
        for i, metric in enumerate(preference_metrics):
            metric_info = metrics_data[metric]
            col = col1 if i % 2 == 0 else col2
            
            with col:
                st.write(f"### {metric_info['name']}")
                st.write(metric_info['description'])
                
                # Create preference range slider with unique key
                min_val, max_val = st.slider(
                    f"Your preferred range for {metric_info['name']}",
                    1, 10, (3, 7),
                    help=f"Low: {metric_info['low_label']} | High: {metric_info['high_label']}",
                    key=f"pref_range_{metric}"
                )
                
                # Store preference in dictionary
                user_preferences[metric] = (min_val, max_val)
                
                # Create importance slider with unique key
                importance = st.slider(
                    f"How important is {metric_info['name']} to you?",
                    1, 10, 5,
                    help="1 = Not important | 10 = Extremely important",
                    key=f"importance_{metric}"
                )
                
                # Store importance in dictionary
                importance_weights[metric] = importance
                
                # Show interpretation of slider values
                st.write(f"*Low (1): {metric_info['rubric']['1']}*")
                st.write(f"*High (10): {metric_info['rubric']['10']}*")
                st.write("---")
        
        # Calculate pathway matches based on user preferences
        st.write("## Your Recommended Pathways")
        
        if st.button("Find Matching Pathways", key="find_match"):
            matches = calculate_pathway_matches(pathways_data, user_preferences, importance_weights)
            
            # Display the top 5 matches
            for i, (pathway_id, match_score, match_explanation) in enumerate(matches[:5]):
                pathway = pathways_data[pathways_data['id'] == pathway_id].iloc[0]
                
                st.markdown(f"### {i+1}. {pathway['name']} - {match_score:.0f}% Match")
                
                # Create two columns for the recommendation display
                rec_col1, rec_col2 = st.columns([1, 2])
                
                with rec_col1:
                    # Display the match explanation
                    st.write("**Why this matches your preferences:**")
                    for metric, explanation in match_explanation.items():
                        st.write(f"- {metrics_data[metric]['name']}: {explanation}")
                    
                    # Buttons for details and roadmap generation
                    if st.button(f"See Full Details #{i+1}", key=f"details_{i}"):
                        st.session_state.selected_pathway = pathway_id
                        st.session_state.active_tab = 1  # Switch to 2x2 Matrix tab
                        st.rerun()
                    
                    if st.button(f"Generate AI Roadmap #{i+1}", key=f"ai_roadmap_{i}"):
                        pathway_details = get_pathway_details(pathways_data, pathway_id)
                        st.session_state.generate_roadmap_for = pathway_details
                        st.session_state.active_tab = 4  # Switch to AI Roadmap tab
                        st.rerun()
                
                with rec_col2:
                    # Create a small visualization of how this pathway matches user preferences
                    matches_data = []
                    for metric in preference_metrics:
                        if metric in pathway['metrics']:
                            min_pref, max_pref = user_preferences[metric]
                            pathway_value = pathway['metrics'][metric]['value']
                            in_range = min_pref <= pathway_value <= max_pref
                            
                            matches_data.append({
                                "Metric": metrics_data[metric]['name'],
                                "Your Preference": f"{min_pref}-{max_pref}",
                                "Pathway Value": pathway_value,
                                "Match": "✅" if in_range else "❌"
                            })
                    
                    st.table(pd.DataFrame(matches_data))
                    
                st.write("---")

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
    # Load the skill graph page
    skill_graph_page()

# About tab
with tab9:
    # About page content
    st.image(DEFAULT_IMAGES["data_viz_concept"], use_container_width=True)
    
    st.write("## About CareerPath Navigator")
    
    st.write("""CareerPath Navigator is a comprehensive career development platform that leverages AI 
to transform skill management, career planning, and professional growth through intelligent, 
data-driven insights.

### Our Mission

To help professionals at any stage understand themselves better, identify fitting career paths, 
and create actionable plans to bridge the gap between their current skills and future goals.

### Key Features

- **Visual Career Exploration**: Compare career options using an interactive 2x2 matrix
- **AI-Powered Analysis**: Extract skills from resumes and analyze job postings
- **Skill Gap Identification**: See which high-demand skills you should develop
- **Personalized Roadmaps**: Get customized step-by-step guidance
- **Project Portfolio**: Document your work to demonstrate your skills

### Technologies

Built with Streamlit, PostgreSQL, and OpenAI integration.
""")
    
    # Add database health status indicator
    with st.expander("System Status", expanded=False):
        from database import test_connection, check_migration_needed
        
        connection_ok = test_connection()
        if connection_ok:
            st.success("✅ Database connection is working properly.")
        else:
            st.error("❌ Database connection failed. Using file-based data instead.")
            
        migration_needed = check_migration_needed()
        if migration_needed:
            st.info("Database schema will be automatically updated on next startup.")
        else:
            st.success("✅ Database schema is up to date.")