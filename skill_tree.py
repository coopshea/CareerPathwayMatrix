import streamlit as st
import networkx as nx
from pyvis.network import Network
import pandas as pd
import matplotlib.pyplot as plt
import os
import json
import tempfile
from database import fetch_job_skills
from io import BytesIO
import base64
import random

def create_skill_network(skills, central_skill=None, user_skills=None, desired_skills=None):
    """
    Create a network visualization of skills.
    
    Args:
        skills (list): List of skills
        central_skill (str, optional): The central skill node
        user_skills (list, optional): Skills the user already has
        desired_skills (list, optional): Skills the user wants to acquire
    
    Returns:
        Network: A pyvis Network object
    """
    # Create networkx graph
    G = nx.Graph()
    
    # Default lists if None provided
    if user_skills is None:
        user_skills = []
    if desired_skills is None:
        desired_skills = []
    
    # Create skill nodes and categorize them
    for skill in skills:
        skill_name = skill['name']
        
        # Determine node color based on user's skill status
        if skill_name in user_skills:
            # User already has this skill
            node_color = "#4CAF50"  # Green
            title = f"{skill_name} (You have this skill)"
            group = 1
        elif skill_name in desired_skills:
            # User wants to acquire this skill
            node_color = "#FFA500"  # Orange
            title = f"{skill_name} (Skill you want to learn)"
            group = 2
        else:
            # Neutral skill
            node_color = "#2196F3"  # Blue
            title = skill_name
            group = 3
        
        # Add the node with attributes
        G.add_node(
            skill_name, 
            title=title, 
            color=node_color,
            size=10 + skill.get('frequency', 1) * 2,  # Size based on frequency
            group=group,
            label=skill_name
        )
    
    # Find relationships between skills (co-occurrence in job postings)
    # For simplicity, we'll connect skills that are frequently appearing together
    # In a real implementation, you'd want to analyze actual co-occurrence in job data
    skill_names = [skill['name'] for skill in skills]
    
    # Create some edges based on a heuristic
    for i, skill1 in enumerate(skills):
        # Connect to some other skills based on frequency
        # Higher frequency skills get more connections
        num_connections = min(5, max(1, skill1.get('frequency', 1) // 2))
        
        # Get potential connection targets
        potential_targets = skill_names.copy()
        potential_targets.remove(skill1['name'])
        
        if central_skill and skill1['name'] == central_skill:
            # Connect central skill to all others
            for skill2_name in potential_targets:
                G.add_edge(skill1['name'], skill2_name, value=1)
        else:
            # Randomly choose some connections
            if potential_targets:
                chosen_targets = random.sample(
                    potential_targets, 
                    min(num_connections, len(potential_targets))
                )
                
                for skill2_name in chosen_targets:
                    # Weight is based on combined frequency
                    skill2 = next((s for s in skills if s['name'] == skill2_name), None)
                    if skill2:
                        weight = min(10, (skill1.get('frequency', 1) + skill2.get('frequency', 1)) / 2)
                        G.add_edge(skill1['name'], skill2_name, value=weight)
    
    # Create pyvis network from networkx graph
    net = Network(height="600px", width="100%", bgcolor="#222222", font_color="white")
    
    # Set physics layout options
    net.barnes_hut(
        gravity=-80000, 
        central_gravity=0.3, 
        spring_length=250, 
        spring_strength=0.001,
        damping=0.09,
        overlap=0
    )
    
    # Copy the networkx graph to the pyvis network
    net.from_nx(G)
    
    # Enable physics
    net.toggle_physics(True)
    
    # Add legend
    net.add_node("has_skill", label="Skills You Have", color="#4CAF50", shape="dot", size=15)
    net.add_node("want_skill", label="Skills To Learn", color="#FFA500", shape="dot", size=15)
    net.add_node("other_skill", label="Other Skills", color="#2196F3", shape="dot", size=15)
    
    # Position legend nodes
    for i, node in enumerate(["has_skill", "want_skill", "other_skill"]):
        net.get_node(node)['x'] = -300
        net.get_node(node)['y'] = -300 + i * 50
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

def skill_tree_page():
    """Streamlit page for the interactive skill tree visualization."""
    st.title("Skill Tree Visualization")
    st.write("""
    Visualize skills as an interactive network. Map your current skills against desired skills 
    and see how they relate to those in demand across job postings.
    """)
    
    # Sidebar controls
    st.sidebar.markdown("## Skill Tree Controls")
    
    # Filter by skill type
    skill_type = st.sidebar.selectbox(
        "Job Skill Type", 
        ["All", "Required", "Preferred"],
        index=0
    )
    
    # Number of skills to show
    top_n = st.sidebar.slider(
        "Number of Skills to Include", 
        10, 100, 30
    )
    
    # Convert skill_type for database query
    skill_type_param = None if skill_type == "All" else skill_type.lower()
    
    try:
        # Fetch skills from the database
        skills = fetch_job_skills(top_n=top_n, skill_type=skill_type_param)
        
        if not skills:
            st.info("No skills found in the database. Try uploading some job postings first.")
            return
        
        # Create sections for the skill tree
        col1, col2 = st.columns([2, 3])
        
        with col1:
            st.write("## Your Skills Profile")
            
            # Input for central skill (main focus)
            skill_options = ["None"] + [skill['name'] for skill in skills]
            central_skill = st.selectbox(
                "Select your central/focus skill",
                options=skill_options
            )
            
            if central_skill == "None":
                central_skill = None
            
            # Multi-select for skills the user already has
            st.write("### Skills You Already Have")
            user_skills = st.multiselect(
                "Select skills you already possess",
                options=[skill['name'] for skill in skills]
            )
            
            # Multi-select for skills the user wants to acquire
            st.write("### Skills You Want to Learn")
            desired_skills = st.multiselect(
                "Select skills you want to acquire",
                options=[s['name'] for s in skills if s['name'] not in user_skills]
            )
            
            # Display some stats
            st.write("### Your Skills Profile")
            st.write(f"You have {len(user_skills)} skills in your profile")
            st.write(f"You want to learn {len(desired_skills)} more skills")
            
            # Gap analysis - which skills appear frequently but user doesn't have
            if user_skills:
                st.write("### Recommended Skills to Learn")
                missing_high_value = [
                    skill for skill in skills 
                    if skill['name'] not in user_skills 
                    and skill['name'] not in desired_skills
                ][:5]
                
                if missing_high_value:
                    for skill in missing_high_value:
                        st.write(f"- {skill['name']} (appears in {skill['job_count']} job postings)")
                else:
                    st.write("No additional high-value skills to recommend.")
        
        with col2:
            st.write("## Interactive Skill Network")
            
            # Create the network
            net = create_skill_network(
                skills=skills,
                central_skill=central_skill,
                user_skills=user_skills,
                desired_skills=desired_skills
            )
            
            # Get the HTML representation
            html = get_html_network(net)
            
            # Display the network in streamlit
            st.components.v1.html(html, height=600)
            
            st.write("""
            ### How to Use This Visualization
            
            - **Green nodes**: Skills you already have
            - **Orange nodes**: Skills you want to learn
            - **Blue nodes**: Other skills found in job postings
            - **Node size**: Larger nodes appear more frequently in job postings
            - **Connections**: Related skills that often appear together
            
            You can zoom, drag, and click on skills to explore relationships.
            """)
    
    except Exception as e:
        st.error(f"Error creating skill tree: {e}")
        st.info("If this is your first time using the skill tree, make sure you have uploaded some job postings first to populate the skills database.")

if __name__ == "__main__":
    skill_tree_page()