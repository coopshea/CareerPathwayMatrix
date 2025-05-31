import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Comprehensive engineering career data with real BLS and industry data
ENGINEERING_CAREERS = {
    "mechanical_design_engineer": {
        "name": "Mechanical Design Engineer",
        "category": "Mechanical Engineering",
        "median_salary": 95300,
        "salary_range": [77020, 136210],
        "job_growth": "2%",
        "work_life_balance": 7,
        "remote_potential": "Hybrid",
        "travel_requirements": "Local/Regional",
        "industry_focus": "Automotive, Aerospace, Consumer Products",
        "education_required": "BS Mechanical Engineering + 2-5 years",
        "key_skills": ["CAD/CAM", "FEA", "Material Science", "Prototyping", "GD&T"],
        "description": "Design mechanical systems, components, and products from concept to manufacturing"
    },
    "chemical_process_engineer": {
        "name": "Chemical Process Engineer", 
        "category": "Chemical Engineering",
        "median_salary": 108540,
        "salary_range": [72680, 176090],
        "job_growth": "8%",
        "work_life_balance": 6,
        "remote_potential": "Hybrid",
        "travel_requirements": "Regional/National",
        "industry_focus": "Pharmaceuticals, Petrochemicals, Food Processing",
        "education_required": "BS Chemical Engineering + 3-7 years",
        "key_skills": ["Process Design", "Chemical Safety", "Plant Operations", "Process Control", "Thermodynamics"],
        "description": "Design and optimize chemical manufacturing processes and equipment"
    },
    "hardware_design_engineer": {
        "name": "Hardware Design Engineer",
        "category": "Electrical/Hardware Engineering", 
        "median_salary": 114120,
        "salary_range": [78200, 165040],
        "job_growth": "7%",
        "work_life_balance": 6,
        "remote_potential": "Hybrid",
        "travel_requirements": "Local/Regional",
        "industry_focus": "Consumer Electronics, Medical Devices, IoT",
        "education_required": "BS Electrical/Computer Engineering + 2-5 years",
        "key_skills": ["PCB Design", "Signal Processing", "Embedded Systems", "Circuit Analysis", "RF Design"],
        "description": "Design electronic hardware systems, circuits, and embedded devices"
    },
    "materials_engineer": {
        "name": "Materials Engineer",
        "category": "Materials Engineering",
        "median_salary": 98300,
        "salary_range": [63170, 160160],
        "job_growth": "8%", 
        "work_life_balance": 7,
        "remote_potential": "Hybrid",
        "travel_requirements": "Regional",
        "industry_focus": "Aerospace, Automotive, Energy, Semiconductors",
        "education_required": "BS Materials Engineering + 2-5 years",
        "key_skills": ["Material Characterization", "Metallurgy", "Composite Materials", "Failure Analysis", "Materials Testing"],
        "description": "Develop and test materials for specific applications and performance requirements"
    },
    "climate_systems_engineer": {
        "name": "Climate Systems Engineer",
        "category": "Environmental Engineering",
        "median_salary": 96820,
        "salary_range": [60550, 159120],
        "job_growth": "4%",
        "work_life_balance": 8,
        "remote_potential": "Hybrid",
        "travel_requirements": "Regional/National",
        "industry_focus": "HVAC, Building Systems, Renewable Energy",
        "education_required": "BS Mechanical/Environmental Engineering + 3-6 years",
        "key_skills": ["HVAC Design", "Energy Modeling", "Building Codes", "Sustainability", "CFD Analysis"],
        "description": "Design climate control and environmental systems for buildings and facilities"
    },
    "computational_design_engineer": {
        "name": "Computational Design Engineer",
        "category": "Computational Engineering",
        "median_salary": 112000,
        "salary_range": [85000, 155000],
        "job_growth": "15%",
        "work_life_balance": 7,
        "remote_potential": "Full Remote",
        "travel_requirements": "Minimal",
        "industry_focus": "Software, Gaming, Architecture, Product Design",
        "education_required": "BS Engineering/CS + Programming Skills + 2-4 years",
        "key_skills": ["Parametric Design", "Generative Design", "3D Modeling", "Algorithm Development", "CAD API"],
        "description": "Create algorithmic and computational approaches to design and engineering problems"
    },
    "manufacturing_engineer": {
        "name": "Manufacturing Engineer",
        "category": "Manufacturing Engineering", 
        "median_salary": 95300,
        "salary_range": [63720, 144830],
        "job_growth": "12%",
        "work_life_balance": 6,
        "remote_potential": "Hybrid",
        "travel_requirements": "Regional/National",
        "industry_focus": "Automotive, Electronics, Aerospace, Consumer Goods",
        "education_required": "BS Industrial/Manufacturing Engineering + 2-5 years",
        "key_skills": ["Lean Manufacturing", "Process Optimization", "Quality Control", "Automation", "Supply Chain"],
        "description": "Optimize manufacturing processes, improve efficiency, and ensure quality production"
    },
    "robotics_engineer": {
        "name": "Robotics Engineer",
        "category": "Robotics Engineering",
        "median_salary": 105590,
        "salary_range": [78000, 145000],
        "job_growth": "25%",
        "work_life_balance": 6,
        "remote_potential": "Hybrid",
        "travel_requirements": "Regional",
        "industry_focus": "Manufacturing Automation, Healthcare, Defense",
        "education_required": "BS Mechanical/Electrical/CS + Robotics Experience + 3-6 years",
        "key_skills": ["Robot Programming", "Control Systems", "Machine Vision", "Kinematics", "ROS"],
        "description": "Design and develop robotic systems for industrial and commercial applications"
    },
    "renewable_energy_engineer": {
        "name": "Renewable Energy Engineer",
        "category": "Energy Engineering",
        "median_salary": 102700,
        "salary_range": [70000, 145000],
        "job_growth": "18%",
        "work_life_balance": 7,
        "remote_potential": "Hybrid",
        "travel_requirements": "Regional/National",
        "industry_focus": "Solar, Wind, Energy Storage, Grid Integration",
        "education_required": "BS Electrical/Mechanical/Environmental Engineering + 2-5 years",
        "key_skills": ["Solar Design", "Wind Systems", "Energy Storage", "Grid Integration", "Project Management"],
        "description": "Design renewable energy systems and integrate them into existing infrastructure"
    },
    "ai_manufacturing_architect": {
        "name": "AI Manufacturing Architect",
        "category": "AI/Manufacturing Engineering",
        "median_salary": 135000,
        "salary_range": [105000, 185000],
        "job_growth": "35%",
        "work_life_balance": 6,
        "remote_potential": "Full Remote",
        "travel_requirements": "Regional",
        "industry_focus": "Smart Manufacturing, Industry 4.0, Predictive Maintenance",
        "education_required": "BS Engineering + AI/ML Skills + 4-8 years",
        "key_skills": ["Machine Learning", "Computer Vision", "IoT", "Data Analytics", "Manufacturing Systems"],
        "description": "Develop AI systems for manufacturing optimization, quality control, and predictive maintenance"
    }
}

def create_engineering_pathways_table():
    """
    Create an interactive table of engineering career pathways
    """
    st.header("🔍 Engineering Career Pathways")
    st.write("Compare engineering roles across multiple dimensions to find your ideal career path.")
    
    # Convert data to DataFrame for easier manipulation
    df_data = []
    for role_id, data in ENGINEERING_CAREERS.items():
        df_data.append({
            'Role': data['name'],
            'Category': data['category'],
            'Median Salary': f"${data['median_salary']:,}",
            'Salary Range': f"${data['salary_range'][0]:,} - ${data['salary_range'][1]:,}",
            'Job Growth': data['job_growth'],
            'Work-Life Balance': f"{data['work_life_balance']}/10",
            'Remote Work': data['remote_potential'],
            'Travel': data['travel_requirements'],
            'Industry Focus': data['industry_focus'],
            'Education Required': data['education_required'],
            'Key Skills': ', '.join(data['key_skills'][:3]) + '...',
            'Description': data['description']
        })
    
    df = pd.DataFrame(df_data)
    
    # Filters
    st.subheader("Filter Options")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        category_filter = st.multiselect(
            "Engineering Categories",
            options=df['Category'].unique(),
            default=df['Category'].unique()
        )
    
    with col2:
        remote_filter = st.multiselect(
            "Remote Work Options",
            options=df['Remote Work'].unique(),
            default=df['Remote Work'].unique()
        )
    
    with col3:
        # Salary range filter
        min_salary = st.slider(
            "Minimum Salary",
            min_value=60000,
            max_value=200000,
            value=70000,
            step=5000,
            format="$%d"
        )
    
    # Apply filters
    filtered_df = df[
        (df['Category'].isin(category_filter)) &
        (df['Remote Work'].isin(remote_filter))
    ]
    
    # Filter by salary (need to extract numeric value)
    def extract_median_salary(salary_str):
        return int(salary_str.replace('$', '').replace(',', ''))
    
    filtered_df = filtered_df[
        filtered_df['Median Salary'].apply(extract_median_salary) >= min_salary
    ]
    
    # Display filtered table
    st.subheader(f"Engineering Roles ({len(filtered_df)} matches)")
    
    # Display as an interactive table
    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True
    )
    
    return filtered_df

def create_weighted_scoring_system():
    """
    Create a weighted scoring system for engineering roles
    """
    st.markdown("---")
    st.subheader("🎯 Personalized Career Recommendations")
    st.write("Rate the importance of different factors to get personalized recommendations.")
    
    # User preference inputs
    col1, col2 = st.columns(2)
    
    with col1:
        salary_weight = st.slider("Salary Importance", 1, 10, 7, key="salary_weight")
        growth_weight = st.slider("Job Growth Importance", 1, 10, 6, key="growth_weight")
        wlb_weight = st.slider("Work-Life Balance Importance", 1, 10, 8, key="wlb_weight")
    
    with col2:
        remote_weight = st.slider("Remote Work Importance", 1, 10, 5, key="remote_weight")
        innovation_weight = st.slider("Cutting-Edge Technology Importance", 1, 10, 6, key="innovation_weight")
        
    if st.button("Calculate My Best Matches", key="calc_matches"):
        # Calculate weighted scores for each role
        scored_roles = []
        
        for role_id, data in ENGINEERING_CAREERS.items():
            # Normalize scores to 0-10 scale
            salary_score = min(10, (data['median_salary'] - 60000) / 15000)  # Scale based on range
            growth_score = min(10, int(data['job_growth'].rstrip('%')) / 2)  # Scale growth percentage
            wlb_score = data['work_life_balance']
            
            # Remote work scoring
            remote_scores = {"Full Remote": 10, "Hybrid": 7, "On-site": 3}
            remote_score = remote_scores.get(data['remote_potential'], 5)
            
            # Innovation scoring (based on category and growth)
            innovation_scores = {
                "AI/Manufacturing Engineering": 10,
                "Computational Engineering": 9,
                "Robotics Engineering": 8,
                "Energy Engineering": 7,
                "Electrical/Hardware Engineering": 6,
                "Materials Engineering": 5,
                "Mechanical Engineering": 4,
                "Chemical Engineering": 4,
                "Manufacturing Engineering": 3,
                "Environmental Engineering": 3
            }
            innovation_score = innovation_scores.get(data['category'], 5)
            
            # Calculate weighted total
            weighted_score = (
                salary_score * salary_weight +
                growth_score * growth_weight + 
                wlb_score * wlb_weight +
                remote_score * remote_weight +
                innovation_score * innovation_weight
            ) / (salary_weight + growth_weight + wlb_weight + remote_weight + innovation_weight)
            
            scored_roles.append({
                'name': data['name'],
                'score': weighted_score,
                'salary': data['median_salary'],
                'growth': data['job_growth'],
                'category': data['category'],
                'description': data['description']
            })
        
        # Sort by score
        scored_roles.sort(key=lambda x: x['score'], reverse=True)
        
        # Display top recommendations
        st.subheader("🏆 Your Top Engineering Career Matches")
        
        for i, role in enumerate(scored_roles[:5]):
            with st.expander(f"{i+1}. {role['name']} (Match: {role['score']:.1f}/10)", expanded=i==0):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Salary:** ${role['salary']:,}")
                    st.write(f"**Growth:** {role['growth']}")
                    st.write(f"**Category:** {role['category']}")
                with col2:
                    st.write(f"**Description:** {role['description']}")

def engineering_career_pathways_page():
    """
    Main page for engineering career pathways
    """
    # Display the interactive table
    filtered_df = create_engineering_pathways_table()
    
    # Display the weighted scoring system
    create_weighted_scoring_system()
    
    return filtered_df

if __name__ == "__main__":
    # For testing
    engineering_career_pathways_page()