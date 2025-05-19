import streamlit as st
import pandas as pd
import numpy as np
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

# Add caveat at the top
st.warning("**FUNCTIONAL PROTOTYPE** - This application demonstrates core functionality (AI integration, skills extraction, etc). UI/UX design is not finalized.")

# Initialize chat messages if not already in session state
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = [
        {"role": "assistant", "content": "Hello! I'm your AI career assistant. How can I help you today?"}
    ]

# AI Chat Assistant Helper for the welcome page using streamlit-chat
def ai_chat_assistant():
    st.write("### AI Career Assistant")
    
    # Initialize the AI mode setting if not already in session state
    if 'use_ai_chat' not in st.session_state:
        st.session_state.use_ai_chat = False
        
    # Add option to toggle between AI-powered and rule-based responses
    with st.expander("Chat Settings", expanded=False):
        st.toggle("Use OpenAI for more intelligent responses", 
                 key="use_ai_chat", 
                 help="When enabled, uses your OpenAI API key to generate more natural and intelligent responses. May be slower than rule-based responses.")
        
        if st.session_state.use_ai_chat:
            import os
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                st.warning("No OpenAI API key found. Please add your API key to enable AI-powered chat.")
            else:
                st.success("OpenAI API key detected. AI-powered chat is enabled.")
    
    # Display chat messages (only show the last 4 messages to reduce rendering load)
    for i, chat_message in enumerate(st.session_state.chat_messages[-4:]):
        if chat_message["role"] == "assistant":
            message(chat_message["content"], key=f"msg_assistant_{i}")
        else:
            message(chat_message["content"], is_user=True, key=f"msg_user_{i}")
    
    # Chat input with auto-submit when Enter is pressed
    user_question = st.text_input("Ask me a question:", key="chat_input", 
                                 on_change=process_input if "chat_input" in st.session_state else None)
    
    # Add a button for those who prefer clicking
    button_col1, button_col2 = st.columns([1, 5])
    with button_col1:
        if st.button("Send", key="send_button"):
            process_input()

# Function to process user input when submitted
def process_input():
    if st.session_state.chat_input.strip():
        # Get the user's question
        user_question = st.session_state.chat_input
        
        # Clear the input field
        st.session_state.chat_input = ""
        
        # Add user message to chat
        st.session_state.chat_messages.append({"role": "user", "content": user_question})
        
        # Check if AI mode is enabled and OpenAI API key is available
        if 'use_ai_chat' in st.session_state and st.session_state.use_ai_chat:
            # Try to get an AI-powered response using OpenAI
            try:
                import os
                from openai import OpenAI
                
                # Get the API key from environment variable
                api_key = os.environ.get("OPENAI_API_KEY")
                if not api_key:
                    response = "I couldn't access the OpenAI API key. Using rule-based responses instead.\n\n" + get_quick_response(user_question)
                else:
                    # Create OpenAI client
                    client = OpenAI(api_key=api_key)
                    
                    # Generate response with context about the application
                    ai_response = client.chat.completions.create(
                        model="gpt-4o",  # Use the latest model
                        messages=[
                            {"role": "system", "content": """You are a helpful career assistant in the CareerPath Navigator application. 
                            You can guide users to different features:
                            - 2x2 Matrix (tab 1): For comparing career paths visually
                            - Find Your Pathway (tab 2): For matching preferences to careers
                            - Basic Roadmap (tab 3): For generating simple career roadmaps
                            - AI Roadmap (tab 4): For generating AI-powered personalized roadmaps
                            - Job Posting (tab 5): For analyzing job opportunities
                            - Skills Analysis (tab 6): For finding high-impact skills in the market
                            - Skill Graph (tab 7): For analyzing user skills and gaps
                            
                            Keep responses friendly, concise and helpful. If the user wants to use a feature, 
                            indicate which tab they should use by setting the active_tab session variable."""},
                            {"role": "user", "content": user_question}
                        ],
                        max_tokens=150
                    )
                    
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
                    response_lower = response.lower()
                    for keyword, tab_idx in tab_keywords.items():
                        if keyword in response_lower:
                            st.session_state.active_tab = tab_idx
                            break
            except Exception as e:
                response = f"I encountered an error with the AI response. Using rule-based responses instead.\n\n" + get_quick_response(user_question)
        else:
            # Use the simple rule-based system for low latency
            response = get_quick_response(user_question)
        
        # Add assistant response to chat
        st.session_state.chat_messages.append({"role": "assistant", "content": response})
        
        # Rerun to update the UI
        st.rerun()

def get_quick_response(question):
    """Provide quick responses based on keywords for low latency"""
    question = question.lower()
    
    # Simple mapping of keywords to responses and tab navigation
    response_map = {
        "compare": (1, "I'll show you the Career Matrix to compare different paths."),
        "career path": (1, "Let's explore career paths in the 2x2 Matrix."),
        "explore": (1, "The Career Matrix is perfect for exploration."),
        "matrix": (1, "Opening the 2x2 Matrix visualization for you."),
        
        "skill": (7, "Let's check out your skills in the Skill Graph."),
        "gap": (7, "The Skill Graph will help identify your skill gaps."),
        "analyze": (7, "I'll help you analyze your skills with our Skill Graph."),
        "resume": (7, "Upload your resume in the Skill Graph tab to analyze your skills."),
        
        "job": (5, "Let's analyze a job posting for you."),
        "posting": (5, "The Job Posting analyzer will help evaluate opportunities."),
        "opportunity": (5, "I'll open the Job Posting analyzer for you."),
        
        "roadmap": (4, "Let's create a career roadmap for you."),
        "plan": (4, "The AI Roadmap generator will help you plan your career."),
        "develop": (4, "Let's develop your career plan with the AI Roadmap."),
        
        "recommend": (2, "Let's find pathways that match your preferences."),
        "match": (2, "The Pathway Finder will help match you with careers."),
        "preference": (2, "I'll help you find careers based on your preferences."),
        
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
    return "I can help you explore career paths, analyze skills, evaluate job opportunities, and more. What specific aspect of your career are you interested in today?"

# Create tabs
tabs = st.tabs([
    "Welcome", "2x2 Matrix", "Find Your Pathway", "Basic Roadmap", "AI Roadmap", 
    "Job Posting", "Skills Analysis", "Skill Graph", "About"
])

# Initialize active tab if not already set
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = 0

# Move to the appropriate tab based on session state
current_tab = st.session_state.active_tab

# Welcome tab content
with tabs[0]:
    if current_tab == 0:  # Only show content if this is the active tab
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
with tabs[1]:
    if current_tab == 1:  # Only show content if this is the active tab
        st.write("## Explore Career Pathways on a 2x2 Matrix")
        
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
            
            # Select x and y axis metrics - add keys
            x_metric = st.selectbox(
                "X-Axis Metric", 
                list(metrics_data.keys()),
                index=list(metrics_data.keys()).index("risk_level") if "risk_level" in metrics_data else 0,
                key="x_axis_metric"
            )
            
            y_metric = st.selectbox(
                "Y-Axis Metric", 
                list(metrics_data.keys()),
                index=list(metrics_data.keys()).index("success_probability") if "success_probability" in metrics_data else 0,
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
with tabs[2]:
    if current_tab == 2:  # Only show content if this is the active tab
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
with tabs[3]:
    if current_tab == 3:  # Only show content if this is the active tab
        # Check if we're coming from a pathway detail view with a pre-selected pathway
        pre_selected_pathway = None
        if 'generate_roadmap_for' in st.session_state:
            pre_selected_pathway = st.session_state.generate_roadmap_for
            # Clear the session state so it doesn't persist
            del st.session_state.generate_roadmap_for
        
        roadmap_generator_page(pre_selected_pathway, pathways_data, metrics_data)

# AI Roadmap tab
with tabs[4]:
    if current_tab == 4:  # Only show content if this is the active tab
        # Check if we're coming from a pathway detail view with a pre-selected pathway
        pre_selected_pathway = None
        if 'generate_roadmap_for' in st.session_state:
            pre_selected_pathway = st.session_state.generate_roadmap_for
            # Clear the session state so it doesn't persist
            del st.session_state.generate_roadmap_for
            
        ai_roadmap_generator_page(pre_selected_pathway, pathways_data, metrics_data)

# Job Posting tab
with tabs[5]:
    if current_tab == 5:  # Only show content if this is the active tab
        job_posting_page(pathways_data, metrics_data)

# Skills Analysis tab
with tabs[6]:
    if current_tab == 6:  # Only show content if this is the active tab
        skills_analysis_page()

# Skill Graph tab
with tabs[7]:
    if current_tab == 7:  # Only show content if this is the active tab
        skill_graph_page()

# About tab
with tabs[8]:
    if current_tab == 8:  # Only show content if this is the active tab
        st.image(DEFAULT_IMAGES["data_viz_concept"], use_container_width=True)
        
        st.write("## About CareerPath Navigator")
        
        st.write("""
        CareerPath Navigator is a comprehensive career development platform that leverages AI 
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