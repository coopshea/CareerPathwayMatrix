import streamlit as st
import pandas as pd
import json

def generate_roadmap(pathway, metrics_data):
    """
    Generate a personalized roadmap for a selected career pathway.
    
    Args:
        pathway (dict): The selected pathway data
        metrics_data (dict): Information about metrics
        
    Returns:
        dict: A structured roadmap with phases and steps
    """
    # Extract key information from the pathway
    name = pathway['name']
    key_skills = pathway.get('key_skills', [])
    metrics = pathway.get('metrics', {})
    
    # Initialize roadmap with phases
    roadmap = {
        "pathway": name,
        "phases": [
            {
                "name": "Research & Preparation (0-6 months)",
                "description": "Build your foundation for this pathway",
                "steps": []
            },
            {
                "name": "Initial Development (6-18 months)",
                "description": "Develop core skills and initial experience",
                "steps": []
            },
            {
                "name": "Growth & Advancement (1.5-3 years)",
                "description": "Expand your expertise and build momentum",
                "steps": []
            },
            {
                "name": "Mastery & Scale (3-5+ years)",
                "description": "Reach advanced levels and maximize opportunities",
                "steps": []
            }
        ]
    }
    
    # Add skill development steps based on key_skills
    if key_skills:
        for i, skill in enumerate(key_skills[:3]):  # Use first 3 skills for the roadmap
            # Add to preparation phase
            roadmap["phases"][0]["steps"].append({
                "title": f"Begin learning {skill}",
                "description": f"Start with fundamentals of {skill} through online courses, books, or workshops"
            })
            
            # Add to initial development phase
            roadmap["phases"][1]["steps"].append({
                "title": f"Apply {skill} in real projects",
                "description": f"Gain practical experience with {skill} through personal projects or entry-level work"
            })
            
            # Add to growth phase (for first 2 skills only)
            if i < 2:
                roadmap["phases"][2]["steps"].append({
                    "title": f"Develop advanced {skill} expertise",
                    "description": f"Master advanced concepts and techniques in {skill}"
                })
    
    # Add network-building steps if network dependency is high
    if 'network_dependency' in metrics and metrics['network_dependency']['value'] > 5:
        roadmap["phases"][0]["steps"].append({
            "title": "Begin building professional network",
            "description": "Join relevant online communities, attend meetups, and connect with professionals in the field"
        })
        roadmap["phases"][1]["steps"].append({
            "title": "Expand professional connections",
            "description": "Attend industry conferences, actively participate in community events, and seek mentorship"
        })
        roadmap["phases"][2]["steps"].append({
            "title": "Build strategic partnerships",
            "description": "Form meaningful collaborations with key players in the industry"
        })
    
    # Add capital-related steps if capital requirements are high
    if 'capital_requirements' in metrics and metrics['capital_requirements']['value'] > 6:
        roadmap["phases"][1]["steps"].append({
            "title": "Explore funding options",
            "description": "Research grants, investors, loans, or bootstrapping strategies appropriate for this pathway"
        })
        roadmap["phases"][2]["steps"].append({
            "title": "Secure initial funding",
            "description": "Develop pitch materials and begin approaching potential funding sources"
        })
    
    # Add scaling steps if scalability is high
    if 'scalability' in metrics and metrics['scalability']['value'] > 6:
        roadmap["phases"][2]["steps"].append({
            "title": "Develop scaling strategy",
            "description": "Create a plan for growing and scaling your operations or impact"
        })
        roadmap["phases"][3]["steps"].append({
            "title": "Implement scaling mechanisms",
            "description": "Put systems and processes in place to effectively scale"
        })
    
    # Add technical specialization steps if technical_specialization is high
    if 'technical_specialization' in metrics and metrics['technical_specialization']['value'] > 7:
        roadmap["phases"][0]["steps"].append({
            "title": "Identify specialized knowledge requirements",
            "description": "Research and list the specialized technical skills needed for success"
        })
        roadmap["phases"][3]["steps"].append({
            "title": "Become a recognized expert",
            "description": "Publish articles, speak at conferences, or create educational content to establish expertise"
        })
    
    # Add successful examples step from the pathway data
    if 'success_examples' in pathway and pathway['success_examples']:
        examples = pathway['success_examples']
        example_str = ", ".join(examples[:3])  # Take first 3 examples
        roadmap["phases"][0]["steps"].append({
            "title": "Study successful examples",
            "description": f"Research and learn from successful examples like {example_str}"
        })
    
    # Add mastery phase - final steps for any pathway
    roadmap["phases"][3]["steps"].append({
        "title": "Refine your unique approach",
        "description": "Develop your personal style and differentiation in this field"
    })
    
    roadmap["phases"][3]["steps"].append({
        "title": "Achieve significant milestones",
        "description": "Work toward major achievements that mark success in this pathway"
    })
    
    return roadmap

def display_roadmap(roadmap):
    """
    Display a personalized roadmap in the Streamlit app.
    
    Args:
        roadmap (dict): The structured roadmap to display
    """
    st.title(f"Personalized Roadmap for {roadmap['pathway']}")
    st.write("This roadmap provides a customized framework for your journey. Adapt it to your specific circumstances and goals.")
    
    for i, phase in enumerate(roadmap["phases"]):
        with st.expander(f"Phase {i+1}: {phase['name']}", expanded=True):
            st.write(f"**{phase['description']}**")
            
            for step in phase["steps"]:
                st.markdown(f"### {step['title']}")
                st.write(step["description"])
            
            if not phase["steps"]:
                st.write("No specific steps available for this phase.")
    
    st.write("---")
    st.write("**Note:** This roadmap is a general guideline. Everyone's journey is unique, and you should adjust these steps based on your background, resources, and goals.")

def roadmap_generator_page(pathway=None, pathways_df=None, metrics_data=None):
    """
    Streamlit page for the roadmap generator.
    
    Args:
        pathway (dict, optional): A pre-selected pathway
        pathways_df (DataFrame): The pathways dataframe
        metrics_data (dict): Information about metrics
    """
    st.title("Career Pathway Roadmap Generator")
    
    if pathway is None and pathways_df is not None:
        # Let user select a pathway
        pathway_options = pathways_df["name"].tolist()
        selected_pathway = st.selectbox("Select a career pathway to generate a roadmap:", pathway_options)
        
        # Get the full pathway data
        pathway = pathways_df[pathways_df["name"] == selected_pathway].iloc[0].to_dict()
    
    if pathway and metrics_data:
        # Generate and display the roadmap
        roadmap = generate_roadmap(pathway, metrics_data)
        display_roadmap(roadmap)
        
        # Download option
        roadmap_json = json.dumps(roadmap, indent=2)
        st.download_button(
            label="Download Roadmap as JSON",
            data=roadmap_json,
            file_name=f"{pathway['id']}_roadmap.json",
            mime="application/json"
        )
    else:
        st.error("Please select a pathway to generate a roadmap.")