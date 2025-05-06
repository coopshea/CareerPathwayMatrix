import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from database import fetch_job_skills

def skills_analysis_page():
    """
    Streamlit page for analyzing skills from uploaded job postings.
    This helps users identify high-impact skills to learn based on job market demand.
    """
    st.title("Skills Analysis")
    st.write("""
    This page analyzes skills extracted from all job postings uploaded to the system.
    Identify high-impact skills to learn based on frequency across job postings.
    """)
    
    # Sidebar controls
    st.sidebar.markdown("## Skills Analysis Controls")
    
    # Filter options
    skill_type = st.sidebar.selectbox(
        "Skill Type", 
        ["All", "Required", "Preferred"],
        index=0
    )
    
    top_n = st.sidebar.slider(
        "Number of Skills to Show", 
        5, 50, 20
    )
    
    # Convert skill_type for database query
    skill_type_param = None if skill_type == "All" else skill_type.lower()
    
    # Fetch skills from database
    try:
        skills = fetch_job_skills(top_n=top_n, skill_type=skill_type_param)
        
        if not skills:
            st.info("No skills found in the database. Try uploading some job postings first.")
            return
        
        # Display results in different formats
        tab1, tab2, tab3 = st.tabs(["Chart", "Table", "Insights"])
        
        with tab1:
            st.write(f"## Top {len(skills)} {skill_type} Skills")
            
            # Create DataFrame for visualization
            skills_df = pd.DataFrame(skills)
            
            # Create horizontal bar chart
            fig, ax = plt.subplots(figsize=(10, max(6, len(skills) * 0.3)))
            
            # Sort the data for the chart
            skills_df = skills_df.sort_values('frequency', ascending=True)
            
            # Plot the horizontal bar chart
            colors = sns.color_palette("viridis", len(skills_df))
            bars = ax.barh(skills_df['name'], skills_df['frequency'], color=colors)
            
            # Add labels and formatting
            ax.set_xlabel('Frequency')
            ax.set_title(f'Top {skill_type} Skills by Frequency')
            ax.set_xlim(0, max(skills_df['frequency']) * 1.1)  # Add a bit of space on the right
            
            # Add the actual values at the end of each bar
            for i, bar in enumerate(bars):
                ax.text(bar.get_width() + 0.1, 
                        bar.get_y() + bar.get_height()/2, 
                        f"{skills_df.iloc[i]['frequency']}",
                        va='center')
            
            st.pyplot(fig)
            
        with tab2:
            # Show tabular data with more details
            st.write("## Skills Frequency Table")
            
            # Create a formatted table
            table_data = []
            for skill in skills:
                table_data.append({
                    "Skill Name": skill['name'],
                    "Frequency": skill['frequency'],
                    "Job Count": skill['job_count'],
                    "Appears In": f"{skill['job_count']} job posting{'s' if skill['job_count'] > 1 else ''}"
                })
            
            # Display as a table
            st.table(pd.DataFrame(table_data))
        
        with tab3:
            # Provide insights about skills
            st.write("## Skills Insights")
            
            # Most frequent skill
            if skills:
                most_frequent = skills[0]
                st.write(f"**Most In-Demand Skill:** {most_frequent['name']} (appears in {most_frequent['job_count']} job postings)")
            
            # Skills that appear in multiple job postings
            multiple_jobs = [skill for skill in skills if skill['job_count'] > 1]
            if multiple_jobs:
                st.write("**Skills Appearing in Multiple Job Postings:**")
                for skill in multiple_jobs[:5]:  # Show top 5
                    st.write(f"- {skill['name']} (appears in {skill['job_count']} job postings)")
                
                if len(multiple_jobs) > 5:
                    st.write(f"... and {len(multiple_jobs) - 5} more")
            
            # General advice
            st.write("""
            ### How to Use This Information
            
            1. **Focus on high-frequency skills** that appear across multiple job postings for maximum career leverage
            2. **Compare required vs. preferred skills** to identify core competencies vs. bonus qualifications
            3. **Use this data to guide your learning path** by prioritizing skills that appear frequently in your target jobs
            4. **Consider skill complementarity** - some skills are more valuable when paired with others
            """)
            
            # Add option to download the data
            skills_csv = pd.DataFrame(skills).to_csv(index=False)
            st.download_button(
                label="Download Skills Data as CSV",
                data=skills_csv,
                file_name="job_skills_analysis.csv",
                mime="text/csv"
            )
    
    except Exception as e:
        st.error(f"Error analyzing skills: {e}")
        st.info("If you're seeing database errors, you may need to update your database schema. Go to the About tab and use the Admin Tools section to update the database.")