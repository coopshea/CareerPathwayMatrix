import streamlit as st
import networkx as nx
from pyvis.network import Network
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import json
import tempfile
from database import fetch_job_skills, JobSkill, Session
from io import BytesIO
import base64
import random
import re

# Define AI skills analysis function
def analyze_resume_skills(resume_text):
    """
    Analyze resume text to extract skills using OpenAI.
    In a real implementation, this would use OpenAI API to extract and rate skills.
    
    Args:
        resume_text (str): The text content of the resume
        
    Returns:
        dict: Dictionary of skills with ratings and context
    """
    # In a real implementation, this would call OpenAI to extract skills
    # For demo purposes, we'll return some sample skills
    sample_skills = {
        "Python Programming": {
            "rating": 4,
            "experience": "5 years experience, created multiple data analysis applications",
            "projects": ["Data visualization dashboard", "ML prediction model"]
        },
        "Data Analysis": {
            "rating": 3,
            "experience": "3 years working with pandas and numpy for data processing",
            "projects": ["Customer behavior analysis", "Sales forecasting"]
        },
        "SQL": {
            "rating": 4,
            "experience": "Extensive experience with database queries and design",
            "projects": ["Database migration project", "Query optimization"]
        },
        "JavaScript": {
            "rating": 2,
            "experience": "Basic knowledge for front-end development",
            "projects": ["Interactive web form"]
        },
        "Project Management": {
            "rating": 3,
            "experience": "Led 3 cross-functional teams on software projects",
            "projects": ["ERP Implementation", "Website redesign"]
        }
    }
    return sample_skills


def process_resume_text(file_content, file_type):
    """
    Process the uploaded resume file and extract text based on file type.
    
    Args:
        file_content: The binary content of the file
        file_type: The MIME type or extension of the file
        
    Returns:
        str: The extracted text content
    """
    # For demo purposes, we'll just return some sample text
    # In a real implementation, this would extract text based on file type
    return "Sample resume text that would be processed by the OpenAI API to extract skills"


def generate_skill_graph(user_skills, job_skills):
    """
    Generate a NetworkX graph of user skills and job skills.
    
    Args:
        user_skills (dict): User's skills with ratings
        job_skills (list): Skills from job postings
        
    Returns:
        nx.Graph: The skill graph
    """
    G = nx.Graph()
    
    # Add user skill nodes
    for skill_name, skill_data in user_skills.items():
        # Size based on skill rating (1-5)
        size = 10 + (skill_data['rating'] * 5)
        G.add_node(
            skill_name, 
            size=size,
            group=1,  # User skills group
            title=f"{skill_name}<br>Your Rating: {skill_data['rating']}/5<br>{skill_data['experience']}",
            skill_type="user",
            rating=skill_data['rating']
        )
    
    # Count job skill frequency
    job_skill_count = {}
    for skill in job_skills:
        name = skill['name']
        if name in job_skill_count:
            job_skill_count[name]['count'] += 1
            job_skill_count[name]['job_ids'].add(skill['job_id'])
        else:
            job_skill_count[name] = {
                'count': 1, 
                'job_ids': {skill['job_id']},
                'type': skill['skill_type']
            }
    
    # Add job skill nodes
    for skill_name, data in job_skill_count.items():
        # Skip if this is already a user skill
        if skill_name in user_skills:
            # Update the existing node with job info
            G.nodes[skill_name]['group'] = 3  # Shared skill group
            G.nodes[skill_name]['title'] += f"<br><br>Also found in {len(data['job_ids'])} job postings"
            G.nodes[skill_name]['job_count'] = len(data['job_ids'])
            G.nodes[skill_name]['skill_type'] = "shared"
            continue
            
        # Size based on how many jobs require this skill
        size = 10 + (len(data['job_ids']) * 5)
        G.add_node(
            skill_name, 
            size=size,
            group=2,  # Job skills group
            title=f"{skill_name}<br>Found in {len(data['job_ids'])} job postings<br>Type: {data['type']}",
            skill_type="job",
            job_count=len(data['job_ids'])
        )
    
    # Add edges between skills
    # Connect user skills to similar job skills
    for user_skill in user_skills:
        for job_skill in job_skill_count:
            if job_skill == user_skill:
                # Self connection for shared skills
                continue
                
            # Simple similarity: check for common words
            user_words = set(re.findall(r'\w+', user_skill.lower()))
            job_words = set(re.findall(r'\w+', job_skill.lower()))
            
            # If there are common meaningful words, add an edge
            common_words = user_words.intersection(job_words)
            if common_words and len(common_words) > 0:
                G.add_edge(
                    user_skill, job_skill, 
                    weight=len(common_words), 
                    title=f"Related skills: {', '.join(common_words)}"
                )
    
    # Connect related job skills to each other
    job_skills_list = list(job_skill_count.keys())
    for i, skill1 in enumerate(job_skills_list):
        for skill2 in job_skills_list[i+1:]:
            # Simple similarity: check for common words
            skill1_words = set(re.findall(r'\w+', skill1.lower()))
            skill2_words = set(re.findall(r'\w+', skill2.lower()))
            
            # If there are common meaningful words, add an edge
            common_words = skill1_words.intersection(skill2_words)
            if common_words and len(common_words) > 0:
                G.add_edge(
                    skill1, skill2, 
                    weight=len(common_words), 
                    title=f"Related skills: {', '.join(common_words)}"
                )
    
    return G


def create_interactive_graph(graph):
    """
    Create an interactive PyVis Network from a NetworkX graph.
    
    Args:
        graph (nx.Graph): The NetworkX graph
        
    Returns:
        pyvis.network.Network: The interactive network
    """
    # Create pyvis network
    net = Network(height="600px", width="100%", bgcolor="#222222", font_color="white")
    
    # Set physics options
    net.barnes_hut(
        gravity=-5000,
        central_gravity=0.3,
        spring_length=150,
        spring_strength=0.05,
        damping=0.09,
        overlap=0
    )
    
    # From networkx graph to pyvis network
    net.from_nx(graph)
    
    # Set node colors based on group
    for node in net.nodes:
        if node['group'] == 1:  # User skills
            node['color'] = "#4CAF50"  # Green
        elif node['group'] == 2:  # Job skills
            node['color'] = "#FFA500"  # Orange
        elif node['group'] == 3:  # Shared skills
            node['color'] = "#9C27B0"  # Purple
        
        # Adjust node size
        node['size'] = node.get('size', 20)
        
        # Set label
        node['label'] = node['id']
    
    # Set edge properties
    for edge in net.edges:
        weight = edge.get('weight', 1)
        edge['width'] = weight * 2
        
    # Add legend
    legend_x = -350
    legend_y = -250
    
    net.add_node("legend_user", label="Your Skills", color="#4CAF50", shape="dot", size=15, x=legend_x, y=legend_y)
    net.add_node("legend_job", label="Job Skills", color="#FFA500", shape="dot", size=15, x=legend_x, y=legend_y+50)
    net.add_node("legend_shared", label="Your Skills Needed in Jobs", color="#9C27B0", shape="dot", size=15, x=legend_x, y=legend_y+100)
    
    # Fix legend positions
    for node in ["legend_user", "legend_job", "legend_shared"]:
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


def identify_skill_gaps(user_skills, job_skills):
    """
    Identify skill gaps between user skills and job requirements.
    
    Args:
        user_skills (dict): User's skills with ratings
        job_skills (list): Skills from job postings
        
    Returns:
        list: Top skills to acquire, sorted by frequency in job postings
    """
    # Count job skill frequency
    job_skill_count = {}
    for skill in job_skills:
        name = skill['name']
        if name in job_skill_count:
            job_skill_count[name]['count'] += 1
            job_skill_count[name]['job_ids'].add(skill['job_id'])
        else:
            job_skill_count[name] = {
                'count': 1, 
                'job_ids': {skill['job_id']},
                'type': skill['skill_type']
            }
    
    # Find missing skills (in jobs but not user's profile)
    missing_skills = []
    for skill_name, data in job_skill_count.items():
        if skill_name not in user_skills:
            missing_skills.append({
                'name': skill_name,
                'job_count': len(data['job_ids']),
                'type': data['type']
            })
    
    # Sort by number of jobs that require this skill
    missing_skills.sort(key=lambda x: x['job_count'], reverse=True)
    
    return missing_skills


def generate_skill_roadmap(user_skills, target_skill, all_skills):
    """
    Generate a roadmap to acquire a target skill.
    
    Args:
        user_skills (dict): User's current skills
        target_skill (str): The skill to acquire
        all_skills (list): All skills data
        
    Returns:
        dict: A roadmap with steps
    """
    # Define skill prerequisites map (in a real implementation, this would be dynamic)
    skill_prerequisites = {
        "Machine Learning": ["Python Programming", "Statistics", "Data Analysis"],
        "Data Science": ["Python Programming", "Statistics", "Data Analysis"],
        "Deep Learning": ["Machine Learning", "Python Programming", "Mathematics"],
        "JavaScript Frameworks": ["JavaScript", "HTML", "CSS"],
        "DevOps": ["Linux", "Cloud Services", "Scripting"],
        "Cloud Architecture": ["DevOps", "Security", "Networking"],
        "Full Stack Development": ["Frontend Development", "Backend Development", "Database Management"],
        "Backend Development": ["Programming", "API Development", "Database Management"],
        "Frontend Development": ["HTML", "CSS", "JavaScript"],
        "Mobile Development": ["Programming", "UI Design", "API Integration"],
        "Data Engineering": ["Programming", "Database Management", "ETL Processes"],
        "UI/UX Design": ["Design Tools", "User Research", "Prototyping"],
        "Cybersecurity": ["Networking", "Operating Systems", "Security Principles"],
        "Project Management": ["Communication", "Planning", "Risk Management"]
    }
    
    # For demonstration, check if skill exists in our map
    if target_skill not in skill_prerequisites:
        # Create a generic roadmap if skill isn't in our map
        return {
            "skill": target_skill,
            "description": f"A personalized roadmap to acquire {target_skill}",
            "prerequisites": [],
            "steps": [
                {
                    "name": f"Learn {target_skill} fundamentals",
                    "resources": [
                        "Take an online course on a platform like Coursera or Udemy",
                        "Read introductory books on the subject",
                        "Follow tutorials on YouTube"
                    ]
                },
                {
                    "name": "Practice with projects",
                    "resources": [
                        "Create small projects to apply what you've learned",
                        "Join online communities for guidance and feedback",
                        "Contribute to open source projects if applicable"
                    ]
                },
                {
                    "name": "Demonstrate your skills",
                    "resources": [
                        "Add projects to your portfolio",
                        "Create a case study showcasing your work",
                        "Take on freelance work to gain experience"
                    ]
                }
            ]
        }
    
    # Check what prerequisites the user already has
    missing_prerequisites = []
    for prereq in skill_prerequisites[target_skill]:
        if prereq not in user_skills:
            missing_prerequisites.append(prereq)
    
    # Create a roadmap with steps
    roadmap = {
        "skill": target_skill,
        "description": f"A personalized roadmap to acquire {target_skill}",
        "prerequisites": skill_prerequisites[target_skill],
        "missing_prerequisites": missing_prerequisites,
        "steps": []
    }
    
    # Add steps for missing prerequisites
    if missing_prerequisites:
        roadmap["steps"].append({
            "name": "Build prerequisite skills",
            "description": f"Before learning {target_skill}, you need to acquire these foundation skills",
            "tasks": [f"Learn {prereq}" for prereq in missing_prerequisites]
        })
    
    # Add core learning steps
    roadmap["steps"].append({
        "name": f"Learn {target_skill} fundamentals",
        "description": "Master the basic concepts and techniques",
        "tasks": [
            "Take an online course or bootcamp",
            "Read books and documentation",
            "Practice with exercises and small projects"
        ]
    })
    
    roadmap["steps"].append({
        "name": "Build practical experience",
        "description": "Apply your knowledge in real-world scenarios",
        "tasks": [
            "Create a portfolio project",
            "Contribute to relevant open-source projects",
            "Solve problems on platforms like Kaggle or GitHub"
        ]
    })
    
    roadmap["steps"].append({
        "name": "Demonstrate expertise",
        "description": "Show what you've learned and get feedback",
        "tasks": [
            "Share your projects on GitHub",
            "Write blog posts about what you've learned",
            "Join communities to discuss and get feedback"
        ]
    })
    
    return roadmap


def display_roadmap(roadmap):
    """
    Display a skill acquisition roadmap in Streamlit.
    
    Args:
        roadmap (dict): The roadmap to display
    """
    st.write(f"## Roadmap to Learn {roadmap['skill']}")
    st.write(roadmap["description"])
    
    # Prerequisites section
    if roadmap["prerequisites"]:
        st.write("### Prerequisites")
        for prereq in roadmap["prerequisites"]:
            if "missing_prerequisites" in roadmap and prereq in roadmap["missing_prerequisites"]:
                st.markdown(f"- ❌ {prereq} (Need to learn)")
            else:
                st.markdown(f"- ✅ {prereq} (You already know this)")
    
    # Steps section
    st.write("### Learning Path")
    for i, step in enumerate(roadmap["steps"]):
        with st.expander(f"Step {i+1}: {step['name']}", expanded=True):
            if "description" in step:
                st.write(step["description"])
            
            if "tasks" in step:
                for task in step["tasks"]:
                    st.markdown(f"- {task}")
            
            if "resources" in step:
                st.write("**Recommended Resources:**")
                for resource in step["resources"]:
                    st.markdown(f"- {resource}")


def add_user_project(user_data, project_info):
    """
    Add a project to the user's profile.
    
    Args:
        user_data (dict): The user's profile data
        project_info (dict): Information about the project
        
    Returns:
        dict: Updated user data
    """
    if "projects" not in user_data:
        user_data["projects"] = []
    
    user_data["projects"].append(project_info)
    
    # Update skills based on project
    for skill in project_info["skills"]:
        if skill in user_data["skills"]:
            # Increment skill rating if not already at max
            if user_data["skills"][skill]["rating"] < 5:
                user_data["skills"][skill]["rating"] += 1
            
            # Add project to skill experience
            if project_info["name"] not in user_data["skills"][skill]["projects"]:
                user_data["skills"][skill]["projects"].append(project_info["name"])
        else:
            # Add new skill
            user_data["skills"][skill] = {
                "rating": 1,
                "experience": f"Used in {project_info['name']} project",
                "projects": [project_info["name"]]
            }
    
    return user_data


def analyze_project_for_skills(project_description, project_link=""):
    """
    Analyze a project to extract skills.
    In a real implementation, this would use OpenAI to analyze the project.
    
    Args:
        project_description (str): Description of the project
        project_link (str): Link to the project (optional)
        
    Returns:
        dict: Project information with extracted skills
    """
    # In a real implementation, this would call OpenAI to analyze the project
    # For demo purposes, we'll extract some keywords
    keywords = ["Python", "Data", "Analysis", "Web", "JavaScript", "App", "Development", 
               "Machine", "Learning", "Database", "SQL", "API", "Frontend", "Backend"]
    
    # Extract skills from description
    skills = []
    for keyword in keywords:
        if keyword.lower() in project_description.lower():
            if keyword == "Python":
                skills.append("Python Programming")
            elif keyword == "Data" or keyword == "Analysis":
                if "Data Analysis" not in skills:
                    skills.append("Data Analysis")
            elif keyword == "JavaScript":
                skills.append("JavaScript")
            elif keyword == "SQL" or keyword == "Database":
                if "SQL" not in skills:
                    skills.append("SQL")
            elif keyword == "Machine" or keyword == "Learning":
                if "Machine Learning" not in skills:
                    skills.append("Machine Learning")
    
    # Generate a title if none provided
    title = project_description.split(".")[0] if "." in project_description else project_description
    if len(title) > 50:
        title = title[:47] + "..."
    
    return {
        "name": title,
        "description": project_description,
        "link": project_link,
        "skills": skills,
        "date_added": "2024-05-06"  # In a real app, use actual date
    }


def skill_graph_page():
    """Streamlit page for the interactive skill graph and roadmap visualizations."""
    st.title("Career Skill Graph & Roadmap")
    
    # Initialize session state for user data
    if "user_skills" not in st.session_state:
        st.session_state.user_skills = {}
    
    if "user_projects" not in st.session_state:
        st.session_state.user_projects = []
    
    # Create tabs for different sections
    profile_tab, visualization_tab, roadmap_tab, projects_tab = st.tabs([
        "Skills Profile", "Skill Graph", "Skill Roadmaps", "My Projects"
    ])
    
    with profile_tab:
        st.write("## Your Skills Profile")
        st.write("Upload your resume or add skills manually to build your profile.")
        
        # Resume upload section
        st.write("### Upload Resume")
        uploaded_file = st.file_uploader("Upload your resume (PDF, DOCX, or TXT)", 
                                       type=["pdf", "docx", "txt"])
        
        if uploaded_file is not None:
            # Display file details
            file_details = {"Filename": uploaded_file.name, 
                           "FileType": uploaded_file.type,
                           "FileSize": f"{uploaded_file.size / 1024:.2f} KB"}
            
            st.write("#### File Details:")
            st.json(file_details)
            
            # Process the resume
            if st.button("Extract Skills from Resume"):
                # Get resume text (in a real app, extract text based on file type)
                resume_text = process_resume_text(uploaded_file.read(), uploaded_file.type)
                
                # Analyze resume with AI (in a real app, call OpenAI)
                extracted_skills = analyze_resume_skills(resume_text)
                
                # Save extracted skills to session state
                st.session_state.user_skills = extracted_skills
                
                st.success("Skills extracted successfully!")
        
        # Display and edit skills
        st.write("### Your Skills")
        
        if st.session_state.user_skills:
            # Show existing skills with edit options
            skills_to_delete = []
            
            for skill, data in st.session_state.user_skills.items():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"**{skill}**")
                
                with col2:
                    new_rating = st.slider(
                        f"Rate your {skill} skills", 
                        min_value=1, 
                        max_value=5, 
                        value=data["rating"],
                        key=f"rating_{skill}"
                    )
                    # Update the rating if changed
                    if new_rating != data["rating"]:
                        st.session_state.user_skills[skill]["rating"] = new_rating
                
                with col3:
                    if st.button("Remove", key=f"remove_{skill}"):
                        skills_to_delete.append(skill)
                
                # Experience text area
                new_experience = st.text_area(
                    f"Your experience with {skill}", 
                    value=data["experience"],
                    key=f"exp_{skill}"
                )
                # Update the experience if changed
                if new_experience != data["experience"]:
                    st.session_state.user_skills[skill]["experience"] = new_experience
                
                st.write("---")
            
            # Remove skills marked for deletion
            for skill in skills_to_delete:
                del st.session_state.user_skills[skill]
                st.rerun()
        else:
            st.info("No skills in your profile yet. Upload your resume or add skills manually.")
        
        # Add skill manually section
        with st.expander("Add Skill Manually", expanded=False):
            new_skill = st.text_input("Skill name")
            new_rating = st.slider("Skill rating", 1, 5, 3)
            new_experience = st.text_area("Your experience with this skill")
            
            if st.button("Add Skill") and new_skill:
                # Add the new skill to session state
                st.session_state.user_skills[new_skill] = {
                    "rating": new_rating,
                    "experience": new_experience,
                    "projects": []
                }
                st.success(f"Added {new_skill} to your profile!")
                st.rerun()
    
    with visualization_tab:
        st.write("## Skill Graph Visualization")
        st.write("""
        This interactive visualization shows the relationship between your skills and job requirements.
        - **Green nodes**: Skills you already have
        - **Orange nodes**: Skills required in job postings
        - **Purple nodes**: Your skills that are also required in jobs
        - **Node size**: Larger nodes represent higher skill ratings or more job demand
        - **Connections**: Skills that are related or often appear together
        """)
        
        # Sidebar filters for job skills
        st.sidebar.markdown("## Skill Graph Controls")
        
        skill_type = st.sidebar.selectbox(
            "Job Skill Type Filter", 
            ["All", "Required", "Preferred"],
            index=0
        )
        
        job_category = st.sidebar.selectbox(
            "Job Category Filter",
            ["All Categories", "Software Development", "Data Science", "Product Management"],
            index=0
        )
        
        # Convert filters for database
        skill_type_param = None if skill_type == "All" else skill_type.lower()
        category_param = None if job_category == "All Categories" else job_category
        
        # Number of skills to show
        top_n = st.sidebar.slider(
            "Number of Job Skills to Include", 
            10, 100, 50
        )
        
        # Check if user has skills
        if not st.session_state.user_skills:
            st.warning("""
            Your skill profile is empty. Please go to the Skills Profile tab to upload your resume
            or add skills manually before using the visualization.
            """)
        else:
            try:
                # Fetch job skills from database
                job_skills = fetch_job_skills(top_n=top_n, skill_type=skill_type_param, category=category_param)
                
                if not job_skills:
                    st.info("""
                    No job skills found in the database matching your filters. 
                    Try uploading some job postings first or changing your filters.
                    """)
                else:
                    # Create the skill graph
                    graph = generate_skill_graph(st.session_state.user_skills, job_skills)
                    
                    # Create the interactive visualization
                    net = create_interactive_graph(graph)
                    
                    # Get the HTML representation
                    html = get_html_network(net)
                    
                    # Display the visualization
                    st.components.v1.html(html, height=600)
                    
                    # Display skill gap analysis
                    missing_skills = identify_skill_gaps(st.session_state.user_skills, job_skills)
                    
                    st.write("## Skill Gap Analysis")
                    st.write("""
                    These are the most in-demand skills from job postings that are missing from your profile.
                    Focus on acquiring these skills to improve your job market value.
                    """)
                    
                    if missing_skills:
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            # Create a dataframe for the top missing skills
                            skill_df = pd.DataFrame(missing_skills[:10])
                            skill_df.columns = ["Skill", "Job Count", "Type"]
                            
                            # Display as a table
                            st.table(skill_df)
                        
                        with col2:
                            # Create a bar chart of the top missing skills
                            if len(missing_skills) > 0:
                                fig, ax = plt.subplots(figsize=(5, 8))
                                y_pos = np.arange(min(10, len(missing_skills)))
                                skills = [s['name'] for s in missing_skills[:10]]
                                counts = [s['job_count'] for s in missing_skills[:10]]
                                
                                ax.barh(y_pos, counts, align='center')
                                ax.set_yticks(y_pos)
                                ax.set_yticklabels(skills)
                                ax.invert_yaxis()  # Labels read top-to-bottom
                                ax.set_xlabel('Number of Job Postings')
                                ax.set_title('Top Skills to Acquire')
                                
                                # Adjust layout
                                plt.tight_layout()
                                st.pyplot(fig)
                    else:
                        st.info("Congratulations! You have all the skills required in the selected job postings.")
            
            except Exception as e:
                st.error(f"Error generating skill graph: {e}")
    
    with roadmap_tab:
        st.write("## Skill Acquisition Roadmaps")
        st.write("""
        Select a skill you want to acquire, and we'll generate a personalized roadmap
        based on your current skills and experience.
        """)
        
        try:
            # Fetch job skills for skill options
            job_skills = fetch_job_skills(top_n=100)
            
            if not job_skills:
                st.info("No job skills found in the database. Try uploading some job postings first.")
            else:
                # Identify skill gaps
                missing_skills = identify_skill_gaps(st.session_state.user_skills, job_skills)
                
                if not missing_skills:
                    st.success("You already have all the skills found in job postings! Consider exploring more advanced skills.")
                    # Use all job skills as options
                    skill_options = list(set(s['name'] for s in job_skills))
                else:
                    # Use top missing skills as options
                    skill_options = [s['name'] for s in missing_skills]
                
                # Let user select a skill to learn
                selected_skill = st.selectbox(
                    "Select a skill you want to learn",
                    options=skill_options
                )
                
                if selected_skill:
                    # Generate a roadmap for the selected skill
                    roadmap = generate_skill_roadmap(
                        st.session_state.user_skills, 
                        selected_skill,
                        job_skills
                    )
                    
                    # Display the roadmap
                    display_roadmap(roadmap)
                    
                    # Option to add this roadmap to profile
                    if st.button("Add This Roadmap to My Profile"):
                        if "roadmaps" not in st.session_state:
                            st.session_state.roadmaps = {}
                        
                        st.session_state.roadmaps[selected_skill] = roadmap
                        st.success(f"Added {selected_skill} roadmap to your profile!")
        
        except Exception as e:
            st.error(f"Error generating skill roadmap: {e}")
    
    with projects_tab:
        st.write("## My Projects Portfolio")
        st.write("""
        Add projects you've worked on to demonstrate your skills and build your portfolio.
        Projects are analyzed for skills, which update your skills profile.
        """)
        
        # Display existing projects
        if st.session_state.user_projects:
            st.write("### Your Projects")
            
            for i, project in enumerate(st.session_state.user_projects):
                with st.expander(f"{project['name']}", expanded=False):
                    st.write(f"**Description:** {project['description']}")
                    
                    if project['link']:
                        st.write(f"**Link:** [{project['link']}]({project['link']})")
                    
                    st.write("**Skills demonstrated:**")
                    for skill in project['skills']:
                        st.markdown(f"- {skill}")
                    
                    st.write(f"**Added on:** {project['date_added']}")
                    
                    if st.button("Remove Project", key=f"remove_project_{i}"):
                        st.session_state.user_projects.pop(i)
                        st.rerun()
        else:
            st.info("You haven't added any projects yet.")
        
        # Add new project
        st.write("### Add New Project")
        
        project_name = st.text_input("Project name")
        project_description = st.text_area("Project description")
        project_link = st.text_input("Project link (optional)")
        
        if st.button("Add Project") and project_description:
            # Analyze project for skills
            project_info = analyze_project_for_skills(project_description, project_link)
            
            if project_name:
                project_info["name"] = project_name
            
            # Add to projects list
            st.session_state.user_projects.append(project_info)
            
            # Update user skills based on project
            user_data = {
                "skills": st.session_state.user_skills,
                "projects": st.session_state.user_projects
            }
            
            updated_user_data = add_user_project(user_data, project_info)
            
            # Update session state
            st.session_state.user_skills = updated_user_data["skills"]
            
            st.success(f"Added {project_info['name']} to your projects!")
            st.write("**Skills detected in this project:**")
            for skill in project_info['skills']:
                st.markdown(f"- {skill}")
            
            st.rerun()


if __name__ == "__main__":
    skill_graph_page()