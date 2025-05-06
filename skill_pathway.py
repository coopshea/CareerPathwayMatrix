import streamlit as st
import networkx as nx
from pyvis.network import Network
import pandas as pd
import matplotlib.pyplot as plt
import os
import json
import tempfile
from database import fetch_job_skills, JobSkill, Session
from io import BytesIO
import base64
import random
from PIL import Image
import io

# Define skill categories and their relationships
SKILL_CATEGORIES = {
    "Programming": {
        "Basic": ["Python Basics", "JavaScript Basics", "HTML/CSS", "SQL Basics"],
        "Intermediate": ["Data Structures", "Algorithms", "API Development", "Web Development"],
        "Advanced": ["System Design", "Machine Learning", "Cloud Architecture", "DevOps"]
    },
    "Data Science": {
        "Basic": ["Statistics", "Data Visualization", "SQL Basics", "Python Basics"],
        "Intermediate": ["Machine Learning Basics", "Data Wrangling", "Feature Engineering", "A/B Testing"],
        "Advanced": ["Deep Learning", "NLP", "Recommender Systems", "Computer Vision"]
    },
    "Business": {
        "Basic": ["Communication", "Presentation Skills", "Project Management", "Excel"],
        "Intermediate": ["Business Analysis", "Product Management", "Market Research", "Leadership"],
        "Advanced": ["Strategy", "Executive Leadership", "Negotiation", "Financial Modeling"]
    }
}

# Define skill prerequisites
SKILL_PREREQUISITES = {
    "Python Basics": [],
    "JavaScript Basics": [],
    "HTML/CSS": [],
    "SQL Basics": [],
    "Data Structures": ["Python Basics"],
    "Algorithms": ["Data Structures"],
    "API Development": ["Python Basics", "JavaScript Basics"],
    "Web Development": ["HTML/CSS", "JavaScript Basics"],
    "System Design": ["Algorithms", "API Development"],
    "Machine Learning": ["Python Basics", "Statistics", "Algorithms"],
    "Cloud Architecture": ["System Design"],
    "DevOps": ["System Design"],
    
    "Statistics": [],
    "Data Visualization": ["Python Basics"],
    "Machine Learning Basics": ["Python Basics", "Statistics"],
    "Data Wrangling": ["Python Basics", "SQL Basics"],
    "Feature Engineering": ["Machine Learning Basics"],
    "A/B Testing": ["Statistics"],
    "Deep Learning": ["Machine Learning"],
    "NLP": ["Deep Learning", "Python Basics"],
    "Recommender Systems": ["Machine Learning"],
    "Computer Vision": ["Deep Learning"],
    
    "Communication": [],
    "Presentation Skills": ["Communication"],
    "Project Management": [],
    "Excel": [],
    "Business Analysis": ["Excel"],
    "Product Management": ["Project Management"],
    "Market Research": ["Excel"],
    "Leadership": ["Communication"],
    "Strategy": ["Leadership"],
    "Executive Leadership": ["Leadership", "Strategy"],
    "Negotiation": ["Communication"],
    "Financial Modeling": ["Excel"]
}

def extract_skills_from_resume(resume_text):
    """
    Placeholder for function that would extract skills from a resume.
    In a real implementation, this would use AI to identify skills.
    
    Args:
        resume_text (str): The text of the resume
        
    Returns:
        list: Extracted skills
    """
    # In a real implementation, this would use OpenAI or similar to extract skills
    # For demo purposes, we'll return some sample skills
    return ["Python Basics", "SQL Basics", "Communication", "Project Management"]


def identify_career_gap(current_skills, target_job_skills):
    """
    Identify skills gap between user's current skills and target job requirements.
    
    Args:
        current_skills (list): List of skills the user already has
        target_job_skills (list): List of skills required for the target job
        
    Returns:
        dict: Gap analysis with missing skills and their importance
    """
    missing_skills = []
    
    for skill in target_job_skills:
        if skill['name'] not in current_skills:
            missing_skills.append({
                'name': skill['name'],
                'frequency': skill['frequency'],
                'job_count': skill['job_count'],
                'importance': 'High' if skill['job_count'] > 1 else 'Medium'
            })
    
    # Sort by importance and frequency
    missing_skills.sort(key=lambda x: (0 if x['importance'] == 'High' else 1, -x['frequency']))
    
    return missing_skills


def create_skill_pathway_graph(user_skills, target_skills, all_skills_data):
    """
    Create a network visualization showing the pathway from user's current skills to target skills.
    
    Args:
        user_skills (list): Skills the user already has
        target_skills (list): Skills the user wants to acquire
        all_skills_data (list): All available skills with metadata
        
    Returns:
        Network: A pyvis Network object
    """
    # Create a directed graph to represent skill pathways
    G = nx.DiGraph()
    
    # We'll build a simple skill tree structure
    # - Current skills as foundation
    # - Missing prerequisites
    # - Target skills at the top
    
    # Convert all_skills_data into a dict for easier lookup
    all_skills_dict = {skill['name']: skill for skill in all_skills_data}
    
    # Add user's current skills (as foundation)
    for skill in user_skills:
        G.add_node(skill, 
                   title=f"{skill} (You already have this skill)",
                   color="#4CAF50",  # Green
                   level=1,
                   size=20,
                   group=1)
    
    # Add target skills (as goals)
    for skill in target_skills:
        skill_name = skill['name']
        skill_freq = skill['frequency'] if 'frequency' in skill else 1
        skill_jobs = skill['job_count'] if 'job_count' in skill else 1
        
        G.add_node(skill_name, 
                   title=f"{skill_name} (Target skill - found in {skill_jobs} job postings)",
                   color="#FFA500",  # Orange
                   level=3,
                   size=15 + skill_freq,
                   group=2)
    
    # Find missing prerequisites for target skills
    # First, get all skills needed to reach target skills
    needed_skills = set()
    for skill in target_skills:
        skill_name = skill['name']
        
        # Check if this skill is in our prerequisite map
        if skill_name in SKILL_PREREQUISITES:
            # Add all prerequisites
            needed_skills.update(SKILL_PREREQUISITES[skill_name])
            
            # Add edges from prerequisites to this skill
            for prereq in SKILL_PREREQUISITES[skill_name]:
                G.add_edge(prereq, skill_name,
                          title=f"{prereq} is needed for {skill_name}",
                          arrows="to",
                          color="#999")
    
    # Now add all missing prerequisites (skills needed but not yet acquired)
    for skill in needed_skills:
        if skill not in user_skills:
            G.add_node(skill,
                      title=f"{skill} (Prerequisite skill needed)",
                      color="#2196F3",  # Blue
                      level=2,
                      size=15,
                      group=3)
            
            # Connect this prerequisite to any user skills that lead to it
            for user_skill in user_skills:
                if user_skill in SKILL_PREREQUISITES.get(skill, []):
                    G.add_edge(user_skill, skill,
                              title=f"{user_skill} helps learn {skill}",
                              arrows="to",
                              color="#999")
    
    # Look for connections from user skills to target skills
    for user_skill in user_skills:
        for target_skill in target_skills:
            target_name = target_skill['name']
            if user_skill in SKILL_PREREQUISITES.get(target_name, []):
                G.add_edge(user_skill, target_name,
                          title=f"{user_skill} helps learn {target_name}",
                          arrows="to",
                          color="#4CAF50",
                          width=2)
    
    # Create pyvis network from networkx graph
    net = Network(height="700px", width="100%", bgcolor="#FFFFFF", font_color="black", directed=True)
    
    # Set physics layout options
    net.barnes_hut(
        gravity=-2000, 
        central_gravity=0.1, 
        spring_length=150, 
        spring_strength=0.05,
        damping=0.09,
        overlap=0
    )
    
    # Enable hierarchical layout
    net.set_options("""
    const options = {
      "layout": {
        "hierarchical": {
          "enabled": true,
          "levelSeparation": 150,
          "nodeSpacing": 200,
          "treeSpacing": 200,
          "direction": "UD"
        }
      },
      "physics": {
        "hierarchicalRepulsion": {
          "centralGravity": 0.0,
          "springLength": 150,
          "springConstant": 0.01,
          "nodeDistance": 120,
          "damping": 0.09
        },
        "minVelocity": 0.75,
        "solver": "hierarchicalRepulsion"
      }
    }
    """)
    
    # Copy the networkx graph to the pyvis network
    net.from_nx(G)
    
    # Add legend
    legend_x = -350
    legend_y = -350
    
    net.add_node("legend_current", label="Skills You Have", color="#4CAF50", shape="dot", size=15, x=legend_x, y=legend_y)
    net.add_node("legend_target", label="Target Skills", color="#FFA500", shape="dot", size=15, x=legend_x, y=legend_y+50)
    net.add_node("legend_prereq", label="Prerequisite Skills", color="#2196F3", shape="dot", size=15, x=legend_x, y=legend_y+100)
    
    # Fix legend positions
    for node in ["legend_current", "legend_target", "legend_prereq"]:
        net.get_node(node)['physics'] = False
    
    return net


def get_html_network(net):
    """Convert the network to html for display in Streamlit"""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as temp_file:
        # Save the pyvis network as html
        net.save_graph(temp_file.name)
        
        # Read the html content
        with open(temp_file.name, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
    # Remove the temporary file
    os.unlink(temp_file.name)
    
    return html_content


def skill_pathway_page():
    """Streamlit page for the interactive skill pathway visualization."""
    st.title("Career Skill Pathway")
    st.write("""
    Visualize your skills journey from your current abilities to your career goals.
    This tool helps identify skill gaps, prerequisites, and learning pathways to reach your target job skills.
    """)
    
    # Sidebar controls
    st.sidebar.markdown("## Skills Pathway Controls")
    
    # Page tabs
    career_tab, upload_tab, demo_tab = st.tabs(["Career Path Visualization", "Upload Resume", "Demo Path"])
    
    with career_tab:
        col1, col2 = st.columns([1.5, 2.5])
        
        with col1:
            st.write("### Your Skills Profile")
            
            # For demo purposes, provide a dropdown to select career path
            career_path = st.selectbox(
                "Select your target career path",
                ["Data Science", "Software Engineering", "Product Management", "Business Analysis"]
            )
            
            # Fetch job skills from the database for the selected career
            skill_type = st.selectbox(
                "Job Skill Type", 
                ["All", "Required", "Preferred"],
                index=0
            )
            
            # Convert skill_type for database query
            skill_type_param = None if skill_type == "All" else skill_type.lower()
            
            try:
                # Fetch skills from the database
                skills = fetch_job_skills(top_n=50, skill_type=skill_type_param)
                
                if not skills:
                    st.info("No skills found in the database. Try uploading some job postings first.")
                    return
                
                # Multi-select for skills the user already has
                st.write("### Skills You Already Have")
                user_skills = st.multiselect(
                    "Select skills you already possess",
                    options=list(set([skill['name'] for skill in skills] + list(SKILL_PREREQUISITES.keys())))
                )
                
                # Section for target skills
                st.write("### Target Job Skills")
                st.info("These are high-impact skills from job postings in your selected career path.")
                
                # For demo purposes, filter to show top skills for the selected career
                # In a real implementation, this would be more sophisticated
                target_skills = []
                for skill in skills[:10]:  # Show top 10 skills
                    target_skills.append(skill)
                    st.write(f"- {skill['name']} (appears in {skill['job_count']} job postings)")
                
                # Gap analysis
                if user_skills:
                    st.write("### Skills Gap Analysis")
                    missing_skills = identify_career_gap(user_skills, target_skills)
                    
                    if missing_skills:
                        st.write("#### Critical skills to develop:")
                        for skill in missing_skills[:5]:
                            st.write(f"- {skill['name']} ({skill['importance']} importance)")
                    else:
                        st.success("You already have all the target skills! Consider more advanced skills.")
            
            except Exception as e:
                st.error(f"Error fetching skills: {e}")
                skills = []
                target_skills = []
        
        with col2:
            st.write("### Your Career Skill Pathway")
            
            if 'skills' in locals() and skills and target_skills and len(user_skills) > 0:
                # Create the skill pathway visualization
                net = create_skill_pathway_graph(user_skills, target_skills, skills)
                
                # Display the network
                html = get_html_network(net)
                st.components.v1.html(html, height=700)
                
                st.write("""
                ### How to Use This Visualization
                
                - **Green nodes**: Skills you already have
                - **Orange nodes**: Target career skills
                - **Blue nodes**: Prerequisite skills you need to develop
                - **Arrows**: Skill development pathways
                
                The visualization shows the most efficient path from your current skills to your career goals.
                """)
            else:
                st.info("Select your current skills and career path to visualize your skill pathway.")
                
                # Example image of what the pathway might look like
                st.image("https://miro.medium.com/max/700/1*ZvpCt76y25QOfdk_k3uGZg.jpeg", 
                         caption="Example skill pathway visualization")
    
    with upload_tab:
        st.write("### Upload Your Resume")
        st.write("""
        Upload your resume to automatically extract your skills.
        This helps create a personalized skill pathway visualization.
        """)
        
        uploaded_file = st.file_uploader("Choose a resume file (PDF, DOCX, or TXT)", 
                                        type=["pdf", "docx", "txt"])
        
        if uploaded_file is not None:
            # Display a preview of the resume
            st.write("#### Resume Preview")
            file_details = {"Filename": uploaded_file.name, 
                           "FileType": uploaded_file.type,
                           "FileSize": f"{uploaded_file.size / 1024:.2f} KB"}
            st.write(file_details)
            
            # Process the resume (in a real implementation, use OpenAI or similar)
            st.write("#### Extracted Skills")
            extracted_skills = extract_skills_from_resume("Sample resume text")
            
            for skill in extracted_skills:
                st.write(f"- {skill}")
            
            if st.button("Save Skills to Profile"):
                st.session_state.user_skills = extracted_skills
                st.success("Skills saved to your profile! Go to the Career Path tab to see your pathway.")
    
    with demo_tab:
        st.write("### Example Learning Pathways")
        st.write("""
        Here are some example career skill pathways to help you understand how skills build upon each other.
        """)
        
        # Example careers
        demo_career = st.selectbox(
            "Select a career pathway to explore",
            ["Data Science", "Software Engineering", "Product Management"]
        )
        
        if demo_career == "Data Science":
            st.write("#### Data Science Pathway")
            st.write("""
            The data science pathway typically starts with foundational skills like Python and statistics,
            then progresses through data manipulation and visualization, before reaching advanced skills
            like machine learning and deep learning.
            """)
            
            # Create a simple network for data science
            demo_user_skills = ["Python Basics", "SQL Basics", "Statistics"]
            demo_target_skills = [
                {"name": "Machine Learning", "frequency": 10, "job_count": 5},
                {"name": "Deep Learning", "frequency": 8, "job_count": 3},
                {"name": "Data Visualization", "frequency": 7, "job_count": 4}
            ]
            
            demo_all_skills = [
                {"name": s, "frequency": 1, "job_count": 1} 
                for s in list(SKILL_PREREQUISITES.keys())
            ]
            
            demo_net = create_skill_pathway_graph(demo_user_skills, demo_target_skills, demo_all_skills)
            demo_html = get_html_network(demo_net)
            st.components.v1.html(demo_html, height=700)
            
            st.write("""
            **Learning order recommendation:**
            1. Start with Python and Statistics fundamentals
            2. Learn Data Wrangling and SQL for data preparation
            3. Progress to Feature Engineering and basic ML models
            4. Move on to Deep Learning for advanced applications
            """)
            
        elif demo_career == "Software Engineering":
            st.write("#### Software Engineering Pathway")
            st.write("""
            Software engineering typically starts with programming fundamentals and progresses
            through data structures and algorithms before reaching system design and architecture.
            """)
            
            # Create a simple network for software engineering
            demo_user_skills = ["Python Basics", "HTML/CSS", "JavaScript Basics"]
            demo_target_skills = [
                {"name": "System Design", "frequency": 10, "job_count": 5},
                {"name": "Cloud Architecture", "frequency": 8, "job_count": 4},
                {"name": "API Development", "frequency": 9, "job_count": 5}
            ]
            
            demo_all_skills = [
                {"name": s, "frequency": 1, "job_count": 1} 
                for s in list(SKILL_PREREQUISITES.keys())
            ]
            
            demo_net = create_skill_pathway_graph(demo_user_skills, demo_target_skills, demo_all_skills)
            demo_html = get_html_network(demo_net)
            st.components.v1.html(demo_html, height=700)
            
            st.write("""
            **Learning order recommendation:**
            1. Master programming fundamentals in Python/JavaScript
            2. Learn Data Structures and Algorithms
            3. Build expertise in API Development and Web Development
            4. Progress to System Design and Cloud Architecture
            """)
            
        elif demo_career == "Product Management":
            st.write("#### Product Management Pathway")
            st.write("""
            Product management combines business, communication, and technical skills.
            The pathway often starts with business fundamentals and project management,
            then incorporates product-specific skills.
            """)
            
            # Create a simple network for product management
            demo_user_skills = ["Communication", "Project Management", "Excel"]
            demo_target_skills = [
                {"name": "Product Management", "frequency": 10, "job_count": 5},
                {"name": "Strategy", "frequency": 7, "job_count": 4},
                {"name": "Market Research", "frequency": 8, "job_count": 4}
            ]
            
            demo_all_skills = [
                {"name": s, "frequency": 1, "job_count": 1} 
                for s in list(SKILL_PREREQUISITES.keys())
            ]
            
            demo_net = create_skill_pathway_graph(demo_user_skills, demo_target_skills, demo_all_skills)
            demo_html = get_html_network(demo_net)
            st.components.v1.html(demo_html, height=700)
            
            st.write("""
            **Learning order recommendation:**
            1. Develop strong communication and presentation skills
            2. Learn project management fundamentals
            3. Develop business analysis and market research capabilities
            4. Progress to product management and strategy
            """)


if __name__ == "__main__":
    skill_pathway_page()