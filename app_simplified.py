import streamlit as st

# Set page config at the very beginning
st.set_page_config(page_title="CareerPath Navigator", layout="wide")

from dataclasses import dataclass, asdict, field
from typing import Optional, Dict, Any, List
from datetime import datetime

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
    
    1. **Analyze** your current skills and job requirements with the **Skill Graph** tab
    2. **Plan** your journey with the **AI Roadmap** tab
    3. **Showcase** your work in the **Project Portfolio** tab
    4. **Explore** career pathways using the **2×2 Matrix** tab
    5. **Discover** matching careers in the **Find Your Pathway** tab
    
    Every journey begins with a single step. Use the tabs above to navigate through the features or ask our 
    AI assistant below for personalized guidance.
    """)
    
    # AI chat assistant
    st.markdown("---")
    st.markdown("### Not sure where to start? Ask our AI Career Assistant")
    
    # Initialize chat messages if not already in session state
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I'm your AI career assistant. How can I help you today?"}
        ]
    
    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Accept user input
    if prompt := st.chat_input("What would you like to know about your career options?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            
            try:
                # Get API key if available
                import os
                api_key = os.environ.get("OPENAI_API_KEY")
                
                if api_key:
                    from openai import OpenAI
                    
                    # Create OpenAI client
                    client = OpenAI(api_key=api_key)
                    
                    # System message for the chat context
                    messages = [
                        {"role": "system", "content": """You are a helpful career assistant in the CareerPath Navigator application. 
                        Guide users to use different features:
                        - 2x2 Matrix: For comparing career paths visually
                        - Find Your Pathway: For matching preferences to careers
                        - AI Roadmap: For generating personalized roadmaps
                        - Job Posting: For analyzing job opportunities
                        - Skill Graph: For analyzing user skills and gaps
                        
                        Keep responses friendly, concise and helpful."""}
                    ]
                    
                    # Add the conversation history
                    for message in st.session_state.messages:
                        messages.append({"role": message["role"], "content": message["content"]})
                    
                    # Generate a response
                    response = client.chat.completions.create(
                        model="gpt-4o", 
                        messages=messages,
                        temperature=0.7,
                        max_tokens=500
                    )
                    
                    full_response = response.choices[0].message.content
                    
                else:
                    # Fallback response if no API key
                    full_response = "I'm here to help you navigate your career options! You can explore different paths in the tabs above, or ask me specific questions about career transitions, skill development, or job hunting strategies."
                
            except Exception as e:
                full_response = f"I'm here to help with career guidance. What specific aspect of your career journey would you like to explore today?"
                print(f"Error generating AI response: {str(e)}")
            
            # Display the response
            response_placeholder.markdown(full_response)
            
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": full_response})

def render_portfolio_tab():
    st.header("📂 Project Portfolio")
    st.write("Upload and organize your projects to showcase your skills and experience.")
    
    # Initialize project list in session state if needed
    if "projects" not in st.session_state:
        st.session_state.projects = []
    
    # Create tabs for different project actions
    upload_tab, view_tab = st.tabs(["Add Project", "View Projects"])
    
    with upload_tab:
        st.subheader("Add a New Project")
        
        # Project details form
        with st.form("project_form", clear_on_submit=True):
            project_name = st.text_input("Project Name", placeholder="e.g., E-commerce Website")
            project_desc = st.text_area("Project Description", placeholder="Describe your project and your role...", height=150)
            project_skills = st.text_input("Skills Used (comma-separated)", placeholder="e.g., Python, React, SQL")
            project_link = st.text_input("Project Link (optional)", placeholder="https://github.com/...")
            
            # File uploader for project documentation/screenshots
            project_file = fu("Upload Project Documentation/Screenshot", 
                           ["pdf", "docx", "txt", "jpg", "png", "gif"], 
                           key="portfolio_upload")
            
            submitted = st.form_submit_button("Add Project")
            
            if submitted:
                if not project_name or not project_desc:
                    st.error("Please provide at least a project name and description.")
                else:
                    # Create new project entry
                    new_project = {
                        "name": project_name,
                        "description": project_desc,
                        "skills": [skill.strip() for skill in project_skills.split(",") if skill.strip()],
                        "link": project_link if project_link else "",
                        "date_added": datetime.now().strftime("%Y-%m-%d"),
                        "file": None,
                        "file_type": None
                    }
                    
                    # Process file if uploaded
                    if project_file:
                        file_content = project_file.read()
                        
                        # Save file content and type
                        new_project["file"] = file_content
                        new_project["file_type"] = project_file.type
                        
                        # Store in user data if available
                        if "user_data" in st.session_state:
                            st.session_state.user_data.portfolio_bytes = file_content
                    
                    # Add project to session state
                    st.session_state.projects.append(new_project)
                    st.success(f"Project '{project_name}' added successfully!")
                    
                    # Update user skills if needed
                    if "user_skills" in st.session_state and new_project["skills"]:
                        for skill in new_project["skills"]:
                            if skill not in st.session_state.user_skills:
                                st.session_state.user_skills[skill] = {
                                    "rating": 3,  # Default rating
                                    "experience": f"Used in project: {project_name}",
                                    "projects": [project_name]
                                }
                            else:
                                # Update existing skill with this project
                                if "projects" not in st.session_state.user_skills[skill]:
                                    st.session_state.user_skills[skill]["projects"] = []
                                
                                if project_name not in st.session_state.user_skills[skill]["projects"]:
                                    st.session_state.user_skills[skill]["projects"].append(project_name)
    
    with view_tab:
        if not st.session_state.projects:
            st.info("No projects added yet. Add some projects in the 'Add Project' tab.")
        else:
            st.subheader("Your Projects")
            
            # Display projects
            for i, project in enumerate(st.session_state.projects):
                with st.expander(f"{project['name']} ({project['date_added']})"):
                    st.markdown(f"**Description:** {project['description']}")
                    
                    if project['skills']:
                        st.markdown(f"**Skills:** {', '.join(project['skills'])}")
                    
                    if project['link']:
                        st.markdown(f"**Link:** [{project['link']}]({project['link']})")
                    
                    # Display file if available
                    if project['file'] is not None:
                        st.markdown("**Attached File:**")
                        
                        # Handle different file types
                        if project['file_type'] and 'image' in project['file_type']:
                            st.image(project['file'], caption=f"Image for {project['name']}")
                        elif project['file_type'] and 'pdf' in project['file_type']:
                            st.markdown(f"PDF file attached (not displayed)")
                        else:
                            st.markdown(f"File attached (not displayed)")
                    
                    # Delete button
                    if st.button("Delete Project", key=f"del_project_{i}"):
                        st.session_state.projects.pop(i)
                        st.success(f"Project deleted.")
                        st.rerun()
            
            # Export portfolio button
            if st.button("Generate Portfolio Report"):
                # This would be a feature to generate a formatted report
                # of all projects, skills, etc.
                st.info("Portfolio report generation is coming soon!")

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

# We've removed the Job & Resume Analysis tab since we've integrated 
# this functionality into the Skill Graph tab, specifically in the Skills Profile subtab

def render_skill_graph_tab():
    st.header("🧩 Skill Graph")
    # Import and use the skill_graph_page function
    from skill_graph import skill_graph_page
    skill_graph_page()

def main():
    
    # Main header
    st.markdown("""
        <div style='text-align: center'>
            <h1>CareerPath Navigator</h1>
            <h3>Find your path, build your skills, achieve your career goals</h3>
        </div>
    """, unsafe_allow_html=True)
    
    tabs = st.tabs([
        "Welcome",
        "Skill Graph",
        "Project Portfolio", 
        "2×2 Matrix",
        "Find Your Pathway",
        "AI Roadmap",
        "About"
    ])

    with tabs[0]:
        render_welcome_tab()

    with tabs[1]:
        render_skill_graph_tab()

    with tabs[2]:
        render_portfolio_tab()

    with tabs[3]:
        # Simple text premium feature message
        st.header("2×2 Matrix - Premium Feature")
        st.write("This premium feature helps you compare different career paths based on key metrics.")
        st.write("Premium features coming soon!")

    with tabs[4]:
        # Simple text premium feature message
        st.header("Find Your Pathway - Premium Feature")
        st.write("This premium feature matches your preferences and skills with optimal career paths.")
        st.write("Premium features coming soon!")
        
    with tabs[5]:
        # Simple text premium feature message
        st.header("AI Roadmap - Premium Feature")
        st.write("This premium feature generates personalized career development plans and guidance.")
        st.write("Premium features coming soon!")

    with tabs[6]:
        st.header("ℹ️ About")
        st.image(DEFAULT_IMAGES["data_viz_concept"], use_container_width=True)
        st.write("""
        CareerPath Navigator is built on Streamlit.  
        Use the tabs above to interact with every feature.  
        Your uploads & questionnaire answers persist as you move between pages.
        """)

if __name__ == "__main__":
    main()