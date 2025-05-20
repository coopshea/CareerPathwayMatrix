import streamlit as st
import pandas as pd
from datetime import datetime
import os
from typing import List, Dict, Any
import json
import base64
import random
from openai import OpenAI

def identify_skill_gaps(user_skills, job_skills):
    """
    Identify skill gaps between user skills and job requirements.
    
    Args:
        user_skills (dict): User's skills with ratings
        job_skills (list): Skills from job postings
        
    Returns:
        list: Top skills to acquire, sorted by frequency in job postings
    """
    # Get user skill names (case-insensitive matching)
    user_skill_names = set(skill.lower() for skill in user_skills.keys())
    
    # Find missing skills
    missing_skills = []
    seen_skills = set()
    
    for skill in job_skills:
        name = skill.get('name', '').lower()
        if name and name not in user_skill_names and name not in seen_skills:
            missing_skills.append(skill)
            seen_skills.add(name)
    
    # Sort by frequency (job count) in descending order
    return sorted(missing_skills, key=lambda x: x.get('frequency', 0), reverse=True)

def render_skill_roadmap_tab():
    """
    Render the Skills Roadmap tab for planning the user's learning journey.
    """
    st.write("Plan your learning journey to acquire important skills for your career.")
    
    if "user_skills" not in st.session_state or not st.session_state.user_skills:
        st.warning("Please add skills in the Skills Profile tab first.")
    else:
        # Get job skills from database
        from database import fetch_job_skills
        job_skills = fetch_job_skills(top_n=100)
        
        if not job_skills:
            st.info("No job skills found in the database. Try uploading some job postings first.")
        else:
            # Identify skill gaps
            missing_skills = identify_skill_gaps(st.session_state.user_skills, job_skills)
            
            # Always include all job skills in the options for better selection
            # This ensures all skills from uploaded job postings are available
            skill_options = list(set(s['name'] for s in job_skills))
            
            # Add success message if no missing skills
            if not missing_skills:
                st.success("You already have all the skills found in job postings! Consider exploring more advanced skills.")
            
            # Add a button to auto-select top skills from job postings
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Auto-select Top 3 In-demand Skills", key="auto_select_skills"):
                    if missing_skills:
                        # Get top 3 missing skills for auto-selection
                        top_skills = [s['name'] for s in missing_skills[:3]]
                        # Update selected skills in session state to preserve across reruns
                        if 'selected_roadmap_skills' not in st.session_state:
                            st.session_state.selected_roadmap_skills = top_skills
                        else:
                            st.session_state.selected_roadmap_skills = list(set(st.session_state.selected_roadmap_skills + top_skills))
                        st.rerun()  # Rerun to update the multiselect
            
            # Let user select multiple skills to learn
            selected_skills = st.multiselect(
                "Select skills you want to learn",
                options=skill_options,
                default=st.session_state.get('selected_roadmap_skills', [])
            )
            
            # Store selected skills in session state
            if selected_skills:
                st.session_state.selected_roadmap_skills = selected_skills
            
            # Create a list of all skills with their frequency information for the AI
            all_job_skills_data = {}
            for skill in job_skills:
                name = skill.get('name', '')
                if name:
                    if name not in all_job_skills_data:
                        all_job_skills_data[name] = {
                            'frequency': 0,
                            'skill_type': skill.get('skill_type', 'general')
                        }
                    all_job_skills_data[name]['frequency'] += 1
            
            # Sort skills by frequency for importance ranking
            ranked_skills = sorted(
                [(name, data['frequency'], data['skill_type']) 
                 for name, data in all_job_skills_data.items()],
                key=lambda x: x[1],
                reverse=True
            )
            
            # Display AI-generated learning path option
            st.subheader("Generate AI Learning Path")
            st.write("Use AI to create a personalized learning path based on in-demand skills and your current skill set.")
            
            # Allow user to select skills or use the multiselect
            if selected_skills:
                st.success(f"You've selected {len(selected_skills)} skills for your learning path.")
            
            # Generate button in the second column
            with col2:
                generate_button = st.button("Generate Optimized Learning Path", key="generate_ai_path")
            
            if generate_button:
                with st.spinner("Creating your personalized skill roadmap..."):
                    # Get skills for analysis - either selected or top skills if none selected
                    target_skills = selected_skills
                    if not target_skills and missing_skills:
                        target_skills = [s['name'] for s in missing_skills[:5]]
                        st.info(f"Using top 5 in-demand skills since none were specifically selected.")
                    
                    if not target_skills:
                        st.warning("No skills identified for learning. Please select skills or upload job postings first.")
                    else:
                        try:
                            # Create a prompt for the OpenAI API with comprehensive context
                            skills_importance = []
                            for name, freq, skill_type in ranked_skills[:20]:  # Top 20 skills for context
                                importance = "required" if skill_type == "required" else "preferred" if skill_type == "preferred" else "general"
                                skills_importance.append(f"{name} (appears in {freq} job postings, {importance})")
                            
                            # Format current skills with ratings
                            current_skills = []
                            for skill, data in st.session_state.user_skills.items():
                                rating = data.get('rating', 3)
                                current_skills.append(f"{skill} (proficiency: {rating}/5)")
                            
                            # Get target skills with importance info
                            target_skills_with_info = []
                            for skill in target_skills:
                                # Find skill in ranked list
                                skill_found = False
                                for name, freq, skill_type in ranked_skills:
                                    if name.lower() == skill.lower():
                                        importance = "required" if skill_type == "required" else "preferred" if skill_type == "preferred" else "general"
                                        target_skills_with_info.append(f"{name} (appears in {freq} job postings, {importance})")
                                        skill_found = True
                                        break
                                if not skill_found:
                                    target_skills_with_info.append(skill)
                            
                            # Create the prompt for the AI model
                            prompt = f"""
                            You are an expert career and skills development advisor creating a personalized learning plan.
                            
                            ## Job Market Context
                            These are the most in-demand skills from job postings, in order of importance:
                            {', '.join(skills_importance)}
                            
                            ## Current Skills
                            The person has these current skills and proficiency levels:
                            {', '.join(current_skills)}
                            
                            ## Target Skills To Learn
                            The person wants to learn these skills (with their job market importance):
                            {', '.join(target_skills_with_info)}
                            
                            ## Your Task
                            Create an intelligent learning roadmap that:
                            1. Analyzes the relationship between current skills and target skills
                            2. Identifies any intermediate skills needed for an efficient learning path
                            3. Prioritizes skills based on job market demand and learning efficiency
                            4. Suggests a clear sequence that minimizes learning time while maximizing job market value
                            5. Includes specific learning resources (courses, books, projects)
                            6. Provides a realistic timeline
                            
                            Use the skill graph concept to identify logical skill relationships and progressions.
                            For example, if they know Python and want to learn machine learning, data analysis
                            might be an intermediate skill to learn first.
                            
                            Format your response with clear headings, bullet points, and a visual learning path
                            if possible using markdown.
                            """
                            
                            # Make the API call
                            client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
                            
                            response = client.chat.completions.create(
                                model="gpt-4o",
                                messages=[
                                    {"role": "system", "content": "You are a career development and learning specialist who creates detailed skill acquisition roadmaps."},
                                    {"role": "user", "content": prompt}
                                ]
                            )
                            
                            if response and response.choices:
                                roadmap_content = response.choices[0].message.content
                                
                                # Display the generated roadmap
                                st.markdown("### Your Personalized Skill Development Plan")
                                st.markdown(roadmap_content)
                                
                                # Add option to save this roadmap using session state to avoid resetting the page
                                col1, col2 = st.columns([3, 1])
                                with col2:
                                    save_key = f"save_plan_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                                    save_button = st.button("Save This Learning Plan", key=save_key)
                                
                                # Store the roadmap content in session state for preservation through reruns
                                temp_roadmap_key = "temp_roadmap_content"
                                if temp_roadmap_key not in st.session_state:
                                    st.session_state[temp_roadmap_key] = roadmap_content
                                
                                # Check if the save button was clicked
                                if save_button:
                                    if "saved_roadmaps" not in st.session_state:
                                        st.session_state.saved_roadmaps = {}
                                    
                                    # Create a name for the roadmap based on selected skills
                                    skills_summary = ", ".join(target_skills[:2])
                                    if len(target_skills) > 2:
                                        skills_summary += f" +{len(target_skills)-2} more"
                                        
                                    # Create a unique timestamp-based name to avoid conflicts
                                    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                                    roadmap_name = f"Skill Plan: {skills_summary} ({timestamp})"
                                        
                                    st.session_state.saved_roadmaps[roadmap_name] = {
                                        "content": roadmap_content,
                                        "date_created": datetime.now().strftime("%Y-%m-%d"),
                                        "skills": target_skills
                                    }
                                    
                                    st.success(f"Learning plan saved successfully!")
                            else:
                                st.error("Could not generate learning plan. Please try again later.")
                        except Exception as e:
                            st.error(f"Error generating learning plan: {str(e)}")
                            st.info("Please check your internet connection or try again later.")
            
            # Always display the saved plans section
            st.subheader("Your Saved Learning Plans")
            
            if "saved_roadmaps" in st.session_state and st.session_state.saved_roadmaps:
                # Display all saved plans in reverse chronological order (newest first)
                plans = list(st.session_state.saved_roadmaps.items())
                # Sort by timestamp in the name (newest first)
                plans.sort(key=lambda x: x[0].split("(")[-1].replace(")", ""), reverse=True)
                
                for name, plan_data in plans:
                    with st.expander(f"{name}"):
                        st.markdown(plan_data["content"])
                        st.caption(f"Created on: {plan_data['date_created']}")
            else:
                st.info("You haven't saved any learning plans yet. Generate and save a plan to see it here.")