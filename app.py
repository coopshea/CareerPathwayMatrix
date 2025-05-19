import streamlit as st
import pandas as pd
import numpy as np
import random
from data import load_data, get_pathway_details, get_metrics_info
from visualizations import create_matrix_visualization
from recommendations import calculate_pathway_matches
from roadmaps import roadmap_generator_page
from ai_roadmap import ai_roadmap_generator_page
from job_postings import job_posting_page
from skills_analysis import skills_analysis_page
from skill_graph import skill_graph_page
from utils import create_pathway_card, DEFAULT_IMAGES

# Configure page
st.set_page_config(
    page_title="CareerPath Navigator",
    page_icon="🧭",
    layout="wide"
)

# Load the data
pathways_data, metrics_data, categories = load_data()

# Initialize session state for current view
if 'current_view' not in st.session_state:
    st.session_state.current_view = 'landing'

# Function to set the current view
def set_view(view_name):
    st.session_state.current_view = view_name
    st.rerun()

# AI Chat Assistant Helper (placeholder for full implementation)
def ai_chat_assistant():
    st.write("### AI Career Assistant")
    st.write("I can help guide you to the right features based on your needs.")
    
    # Initial questions to help route the user
    initial_questions = [
        "I'm considering changing careers and need to explore options",
        "I want to understand my skills and identify gaps",
        "I need to evaluate if a job opportunity aligns with my goals",
        "I'm looking to create a roadmap for my career development",
        "I'm not sure where to start - can you ask me some questions?"
    ]
    
    selected_question = st.selectbox(
        "What brings you here today?", 
        initial_questions
    )
    
    if st.button("Get Guidance"):
        if "changing careers" in selected_question:
            st.info("The Career Matrix will help you compare different pathways. Let's take you there!")
            st.session_state.ai_recommendation = "matrix"
        elif "skills" in selected_question:
            st.info("The Skills Graph will help you understand your current skills and identify gaps. Let's go there!")
            st.session_state.ai_recommendation = "skill_graph"
        elif "job opportunity" in selected_question:
            st.info("The Job Posting Analysis will help you evaluate specific opportunities. Let's check it out!")
            st.session_state.ai_recommendation = "job_posting"
        elif "roadmap" in selected_question:
            st.info("The AI Roadmap Generator will create a personalized development plan. Let's explore that!")
            st.session_state.ai_recommendation = "ai_roadmap"
        else:
            # More detailed conversation flow for undecided users
            st.write("Let me ask you a few questions to help guide you:")
            
            career_stage = st.radio(
                "Where are you in your career journey?",
                ["Just starting out", "Mid-career", "Looking to make a change", "Advancing in current field"]
            )
            
            main_goal = st.radio(
                "What's your primary goal right now?",
                ["Explore different career options", "Develop specific skills", "Find better opportunities", "Create a long-term plan"]
            )
            
            if st.button("Get Personalized Recommendation"):
                # Simple decision tree for recommendations
                if career_stage == "Looking to make a change" or main_goal == "Explore different career options":
                    st.success("Based on your situation, I recommend starting with the Career Matrix to explore different pathways!")
                    st.session_state.ai_recommendation = "matrix"
                elif main_goal == "Develop specific skills":
                    st.success("Based on your situation, I recommend the Skills Graph to identify high-value skills to develop!")
                    st.session_state.ai_recommendation = "skill_graph"
                elif main_goal == "Find better opportunities":
                    st.success("I recommend starting with the Job Posting Analysis to evaluate specific opportunities!")
                    st.session_state.ai_recommendation = "job_posting"
                else:
                    st.success("The AI Roadmap Generator would be perfect for creating your long-term development plan!")
                    st.session_state.ai_recommendation = "ai_roadmap"

    # Handle navigation based on AI recommendation
    if 'ai_recommendation' in st.session_state:
        recommendation = st.session_state.ai_recommendation
        
        if recommendation == "matrix":
            if st.button("Go to Career Matrix"):
                set_view('matrix')
        elif recommendation == "skill_graph":
            if st.button("Go to Skills Graph"):
                set_view('skill_graph')
        elif recommendation == "job_posting":
            if st.button("Go to Job Posting Analysis"):
                set_view('job_posting')
        elif recommendation == "ai_roadmap":
            if st.button("Go to AI Roadmap Generator"):
                set_view('ai_roadmap')

# Main navigation for different views
if st.session_state.current_view == 'landing':
    # Landing Page
    st.markdown("""
        <div style='text-align: center'>
            <h1>CareerPath Navigator</h1>
            <h3>Find your path, build your skills, achieve your career goals</h3>
        </div>
    """, unsafe_allow_html=True)
    
    st.write("### For professionals at any stage seeking clarity and direction in their career journey")
    
    # Two-column layout for main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("## How can we help you today?")
        
        # User scenario buttons with clear icons and descriptions
        scenario_cols = st.columns(2)
        
        with scenario_cols[0]:
            st.markdown("#### Explore Career Options")
            if st.button("📊 I want to compare different career paths", use_container_width=True):
                set_view('matrix')
                
            st.markdown("#### Understand Your Skills")
            if st.button("🧩 I want to analyze my skills and identify gaps", use_container_width=True):
                set_view('skill_graph')
                
            st.markdown("#### Evaluate Job Opportunities")
            if st.button("🔍 I want to analyze a job posting", use_container_width=True):
                set_view('job_posting')
        
        with scenario_cols[1]:
            st.markdown("#### Get Personalized Recommendations")
            if st.button("💡 I want to find career paths that match my preferences", use_container_width=True):
                set_view('recommendations')
                
            st.markdown("#### Create Development Plans")
            if st.button("🛣️ I want a roadmap for my career development", use_container_width=True):
                set_view('ai_roadmap')
                
            st.markdown("#### Analyze Market Demands")
            if st.button("📈 I want to identify high-impact skills to learn", use_container_width=True):
                set_view('skills_analysis')
    
    with col2:
        # AI chat assistant
        st.markdown("""
            <div style='background-color: #f0f2f6; padding: 20px; border-radius: 10px;'>
                <h3 style='text-align: center;'>Not sure where to start?</h3>
            </div>
        """, unsafe_allow_html=True)
        
        ai_chat_assistant()
    
    # Bottom navigation bar
    st.markdown("---")
    nav_cols = st.columns(4)
    with nav_cols[0]:
        st.markdown("#### Full Feature Menu")
    with nav_cols[1]:
        if st.button("About This Tool"):
            set_view('about')
    with nav_cols[2]:
        if st.button("View All Features"):
            # Create tabs for different sections when View All Features is clicked
            st.session_state.current_view = 'all_features'
            st.rerun()
    with nav_cols[3]:
        pass  # Reserved for future use
            
else:
    # Create header with navigation back to landing page
    header_cols = st.columns([1, 3, 1])
    with header_cols[0]:
        if st.button("← Back to Home"):
            set_view('landing')
    with header_cols[1]:
        st.markdown("""
            <div style='text-align: center'>
                <h2>CareerPath Navigator</h2>
            </div>
        """, unsafe_allow_html=True)
    with header_cols[2]:
        pass  # Reserved for future use
        
    # Create tabs for different sections only when not on landing page
    if st.session_state.current_view == 'all_features':
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
            "2x2 Matrix", "Find Your Pathway", "Basic Roadmap", "AI Roadmap", 
            "Job Posting", "Skills Analysis", "Skill Graph", "About"
        ])
    else:
        # For individual feature views, create hidden tabs but only show the selected one
        tab_names = ["2x2 Matrix", "Find Your Pathway", "Basic Roadmap", "AI Roadmap", 
                    "Job Posting", "Skills Analysis", "Skill Graph", "About"]
        tabs = st.tabs(tab_names)
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = tabs
        
        # Map view names to tab indices
        view_to_tab = {
            'matrix': 0,
            'recommendations': 1,
            'roadmap': 2,
            'ai_roadmap': 3,
            'job_posting': 4,
            'skills_analysis': 5,
            'skill_graph': 6,
            'about': 7
        }
        
        # Show only the selected tab
        if st.session_state.current_view in view_to_tab:
            # This is a workaround since Streamlit doesn't allow programmatic tab selection
            st.session_state.active_tab = view_to_tab[st.session_state.current_view]

with tab1:
    st.write("## Explore Career Pathways on a 2x2 Matrix")
    
    # Sidebar for matrix controls
    st.sidebar.markdown("## Matrix Controls")
    
    # Category filters
    selected_categories = st.sidebar.multiselect(
        "Filter by Category",
        ["All"] + categories,
        default=["All"]
    )
    
    if "All" in selected_categories:
        filtered_pathways = pathways_data
    else:
        filtered_pathways = pathways_data[pathways_data['category'].isin(selected_categories)]
    
    # Select x and y axis metrics
    x_metric = st.sidebar.selectbox(
        "X-Axis Metric", 
        list(metrics_data.keys()),
        index=list(metrics_data.keys()).index("risk_level") if "risk_level" in metrics_data else 0
    )
    
    y_metric = st.sidebar.selectbox(
        "Y-Axis Metric", 
        list(metrics_data.keys()),
        index=list(metrics_data.keys()).index("success_probability") if "success_probability" in metrics_data else 0
    )
    
    # Additional info for selected metrics
    st.sidebar.markdown(f"### {metrics_data[x_metric]['name']}")
    st.sidebar.write(metrics_data[x_metric]['description'])
    st.sidebar.markdown(f"### {metrics_data[y_metric]['name']}")
    st.sidebar.write(metrics_data[y_metric]['description'])
    
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
                    format_func=lambda x: metrics_data[x]['name']
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
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Generate Basic Roadmap"):
                    # Set a session state variable to indicate we want to switch to the basic roadmap tab
                    # with this pathway pre-selected
                    st.session_state.generate_roadmap_for = pathway_details
                    # Switch to the basic roadmap tab (index 2)
                    st.experimental_set_query_params(tab="Basic Roadmap")
                    st.rerun()
            with col2:
                if st.button("Generate AI-Powered Roadmap"):
                    # Set a session state variable to indicate we want to switch to the AI roadmap tab
                    # with this pathway pre-selected
                    st.session_state.generate_roadmap_for = pathway_details
                    # Switch to the AI roadmap tab (index 3)
                    st.experimental_set_query_params(tab="AI Roadmap Generator")
                    st.rerun()

with tab2:
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
        
        for q in questions:
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
            
            # Create preference range slider
            min_val, max_val = st.slider(
                f"Your preferred range for {metric_info['name']}",
                1, 10, (3, 7),
                help=f"Low: {metric_info['low_label']} | High: {metric_info['high_label']}"
            )
            
            # Store preference in dictionary
            user_preferences[metric] = (min_val, max_val)
            
            # Create importance slider
            importance = st.slider(
                f"How important is {metric_info['name']} to you?",
                1, 10, 5,
                help="1 = Not important | 10 = Extremely important"
            )
            
            # Store importance in dictionary
            importance_weights[metric] = importance
            
            # Show interpretation of slider values
            st.write(f"*Low (1): {metric_info['rubric']['1']}*")
            st.write(f"*High (10): {metric_info['rubric']['10']}*")
            st.write("---")
    
    # Calculate pathway matches based on user preferences
    st.write("## Your Recommended Pathways")
    
    if st.button("Find Matching Pathways"):
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
                    st.rerun()
                
                if st.button(f"Generate AI Roadmap #{i+1}", key=f"ai_roadmap_{i}"):
                    pathway_details = get_pathway_details(pathways_data, pathway_id)
                    st.session_state.generate_roadmap_for = pathway_details
                    st.experimental_set_query_params(tab="AI Roadmap Generator")
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

with tab3:
    # Basic Roadmap Generator Tab
    # Check if we're coming from a pathway detail view with a pre-selected pathway
    pre_selected_pathway = None
    if 'generate_roadmap_for' in st.session_state:
        pre_selected_pathway = st.session_state.generate_roadmap_for
        # Clear the session state so it doesn't persist
        del st.session_state.generate_roadmap_for
    
    roadmap_generator_page(pre_selected_pathway, pathways_data, metrics_data)

with tab4:
    # AI-Powered Roadmap Generator Tab
    ai_roadmap_generator_page(pre_selected_pathway, pathways_data, metrics_data)

with tab5:
    # Job Posting Tab
    job_posting_page(pathways_data, metrics_data)
    
with tab6:
    # Skills Analysis Tab
    skills_analysis_page()
    
with tab7:
    # Skill Graph Tab
    skill_graph_page()
    
with tab8:
    st.image(DEFAULT_IMAGES["data_viz_concept"], use_container_width=True)
    
    st.write("## About This Tool")
    
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
            st.info("Database schema will be automatically updated on next restart.")
        else:
            st.success("✅ Database schema is up to date.")
    
    st.markdown("""
    ### Tool Purpose
    This visualization tool applies forecasting methodology to map potential pathways to $10 million in wealth. 
    By systematically analyzing 18 different parameters—from risk level to knowledge half-life—across diverse career options, 
    it helps identify which paths align with your personal circumstances and preferences. The tool doesn't just show what's possible; 
    it helps you understand the tradeoffs inherent in each choice.
    
    ### Theoretical Foundation
    This approach is inspired by forecaster Paul Saffo's methodologies, which use parameter mapping to plot potential futures based on key variables. 
    By visualizing career options on 2x2 matrices, we can identify clusters of opportunity and better understand the relationships between different 
    variables like risk and reward, time investment and expected value, or control and scalability.
    
    ### Expected Value Framework
    The tool incorporates an expected value framework that multiplies potential returns by probability of success. For example, a pathway with a 1% 
    chance of yielding $10 million has an expected value of $100,000. This allows for comparing dissimilar options on a level playing field. 
    While an entrepreneurial path might have low probability but high ceiling, a specialized professional path might offer more certainty with a lower maximum return.
    
    ### Research Methodology
    This tool combines research from hundreds of sources including industry reports, academic studies, and career outcome data. 
    Each pathway is scored on a 1-10 scale across multiple dimensions, with sources and evidence provided for transparency.
    
    ### How to Use This Tool
    1. Start by exploring the 2x2 matrix to compare pathways along different dimensions
    2. Click on specific pathways to see detailed information and evidence
    3. Use the preference sliders to input your own priorities and constraints
    4. Get recommendations for pathways that match your personal profile
    5. Investigate the recommended pathways to understand why they match your preferences
    
    Remember that this tool is meant to inform your decision-making process, not to provide a definitive answer on what career path you should choose.
    The ultimate decision should take into account your unique skills, interests, and circumstances.
    """)
    
    # Images section
    st.write("## Career Pathway Decision Making")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.image(DEFAULT_IMAGES["career_decision_1"], use_container_width=True)
        st.caption("Identifying key decision points in career paths")
    
    with col2:
        st.image(DEFAULT_IMAGES["career_decision_2"], use_container_width=True)
        st.caption("Evaluating multiple options systematically")
    
    with col3:
        st.image(DEFAULT_IMAGES["career_decision_3"], use_container_width=True)
        st.caption("Making data-informed career choices")

# Footer
st.markdown("""
---
<div style='text-align: center'>
<p>This tool is provided for informational purposes only. Career outcomes will vary based on individual circumstances, market conditions, and numerous other factors.</p>
</div>
""", unsafe_allow_html=True)
