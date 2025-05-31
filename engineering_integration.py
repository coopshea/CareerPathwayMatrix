"""
Integration script to add engineering careers to the original pathway data structure
"""

from database import init_db, Pathway
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import os
from engineering_careers import ENGINEERING_CAREERS

def convert_engineering_to_pathways():
    """
    Convert engineering careers to the original pathway format with proper metrics
    """
    session = get_session()
    
    for career_id, career_data in ENGINEERING_CAREERS.items():
        # Check if this pathway already exists
        existing = session.query(Pathway).filter_by(id=f"eng_{career_id}").first()
        if existing:
            continue
            
        # Map engineering data to original metrics format
        salary = career_data['median_salary']
        growth_rate = int(career_data['job_growth'].rstrip('%')) if career_data['job_growth'].rstrip('%').isdigit() else 5
        wlb = career_data['work_life_balance']
        
        # Create metrics using the original structure but mapped from engineering data
        metrics = {
            'risk_level': {'value': max(1, min(10, 11 - wlb))},  # Higher WLB = Lower risk
            'capital_requirements': {'value': max(1, min(10, 3))},  # Most engineering jobs need education, not capital
            'technical_specialization': {'value': 8},  # Engineering is highly technical
            'network_dependency': {'value': 4},  # Moderate networking needed
            'scalability': {'value': 6 if 'Software' in career_data.get('super_category', '') else 4},
            'control': {'value': wlb},
            'geographic_dependency': {'value': 3 if 'Software' in career_data.get('super_category', '') else 6},
            'skill_transfer': {'value': 8},  # Engineering skills are transferable
            'time_to_return': {'value': 4},  # 4-year degree typically required
            'success_probability': {'value': min(10, max(1, growth_rate))},
            'optionality': {'value': 7},  # Engineering provides good career options
            'terminal_value': {'value': max(1, min(10, salary / 25000))},
            'expected_value_10yr': {'value': max(1, min(10, salary / 20000))},
            'competition': {'value': 7 if 'Software' in career_data.get('super_category', '') else 5},
            'social_impact': {'value': 8 if 'Environmental' in career_data.get('category', '') else 6},
            'reversibility': {'value': 6},  # Can change engineering disciplines
            'team_dependency': {'value': 6},  # Most engineering is collaborative
            'regulatory_barriers': {'value': 4 if 'Civil' in career_data.get('category', '') else 2},
            'knowledge_half_life': {'value': 4 if 'Software' in career_data.get('super_category', '') else 7}
        }
        
        pathway = Pathway(
            id=f"eng_{career_id}",
            name=career_data['name'],
            category='Engineering',
            super_category=career_data.get('super_category', 'Engineering'),
            description=career_data.get('description', f"Career in {career_data['name']}"),
            target_customers=career_data.get('target_customers', 'Professionals interested in engineering'),
            success_examples=[f"Senior {career_data['name']} at major companies"],
            key_skills=career_data.get('key_skills', ['Technical skills', 'Problem solving']),
            metrics=metrics,
            rationale={
                'salary_basis': f"Median salary: ${salary:,}",
                'growth_basis': f"Job growth: {career_data['job_growth']}",
                'wlb_basis': f"Work-life balance: {wlb}/10"
            },
            is_job_posting=False,
            pathway_type='engineering_career',
            median_salary=salary,
            salary_range_min=career_data.get('salary_range', {}).get('min', salary * 0.8),
            salary_range_max=career_data.get('salary_range', {}).get('max', salary * 1.3),
            job_growth_rate=career_data['job_growth'],
            work_life_balance_score=wlb,
            travel_requirements=career_data.get('travel_requirements', 'Minimal'),
            industry_focus=career_data.get('industry_focus', 'Engineering'),
            education_required=career_data.get('education_required', 'Bachelor\'s degree')
        )
        
        session.add(pathway)
    
    session.commit()
    session.close()
    print(f"Added {len(ENGINEERING_CAREERS)} engineering careers to original pathway structure")

if __name__ == "__main__":
    convert_engineering_to_pathways()