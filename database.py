import os
import json
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Float, JSON, MetaData, Table, Text, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Get database URL from environment variables
DATABASE_URL = os.environ.get('DATABASE_URL')

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)
Base = declarative_base()
Session = sessionmaker(bind=engine)

# Define database models
class Pathway(Base):
    __tablename__ = 'pathways'
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    description = Column(Text)
    target_customers = Column(Text)
    success_examples = Column(JSON)
    key_skills = Column(JSON)
    metrics = Column(JSON)
    rationale = Column(JSON)
    is_job_posting = Column(Boolean, default=False)  # Flag to identify job postings
    job_data = Column(JSON, nullable=True)  # Original job data from analysis
    date_added = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'description': self.description,
            'target_customers': self.target_customers,
            'success_examples': self.success_examples,
            'key_skills': self.key_skills,
            'metrics': self.metrics,
            'rationale': self.rationale,
            'is_job_posting': self.is_job_posting if self.is_job_posting is not None else False,
            'job_data': self.job_data,
            'date_added': self.date_added.isoformat() if self.date_added else None
        }
    
class Metric(Base):
    __tablename__ = 'metrics'
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    low_label = Column(String)
    high_label = Column(String)
    rubric = Column(JSON)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'low_label': self.low_label,
            'high_label': self.high_label,
            'rubric': self.rubric
        }

class JobSkill(Base):
    __tablename__ = 'job_skills'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, index=True)  # The skill name
    skill_type = Column(String)  # Required, preferred, or general
    job_id = Column(String)  # Reference to the job posting pathway
    job_title = Column(String)  # Job title the skill is associated with
    category = Column(String)  # Category of job the skill is associated with
    frequency = Column(Integer, default=1)  # How many times this skill appears
    date_added = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'skill_type': self.skill_type,
            'job_id': self.job_id,
            'job_title': self.job_title,
            'category': self.category,
            'frequency': self.frequency,
            'date_added': self.date_added.isoformat() if self.date_added else None
        }

# Create tables if they don't exist
def init_db():
    Base.metadata.create_all(engine)
    
# Import data from simplerData.py into the database
def import_simpler_data():
    # Check if data exists in database first
    session = Session()
    existing_pathways = session.query(Pathway).count()
    
    if existing_pathways > 0:
        print(f"Database already contains {existing_pathways} pathways. Skipping import.")
        session.close()
        return
    
    try:
        with open('simplerData.py', 'r') as file:
            simpler_data = eval(file.read())
            
            # Import metrics
            for metric_id, metric_data in simpler_data.get('metrics', {}).items():
                metric = Metric(
                    id=metric_id,
                    name=metric_data.get('name', ''),
                    description=metric_data.get('description', ''),
                    low_label=metric_data.get('low_label', ''),
                    high_label=metric_data.get('high_label', ''),
                    rubric=metric_data.get('rubric', {})
                )
                session.add(metric)
            
            # Import pathways
            for pathway_data in simpler_data.get('pathways', []):
                pathway = Pathway(
                    id=pathway_data.get('id', ''),
                    name=pathway_data.get('name', ''),
                    category=pathway_data.get('category', ''),
                    description=pathway_data.get('description', ''),
                    target_customers=pathway_data.get('target_customers', ''),
                    success_examples=pathway_data.get('success_examples', []),
                    key_skills=pathway_data.get('key_skills', []),
                    metrics=pathway_data.get('metrics', {}),
                    rationale=pathway_data.get('rationale', {})
                )
                session.add(pathway)
            
            session.commit()
            print("Successfully imported data into the database")
            
    except Exception as e:
        session.rollback()
        print(f"Error importing data: {e}")
    finally:
        session.close()

# Fetch data from the database
def fetch_pathways():
    session = Session()
    try:
        pathways = session.query(Pathway).all()
        return [pathway.to_dict() for pathway in pathways]
    finally:
        session.close()

def fetch_metrics():
    session = Session()
    try:
        metrics = session.query(Metric).all()
        metrics_dict = {}
        for metric in metrics:
            metrics_dict[metric.id] = metric.to_dict()
        return metrics_dict
    finally:
        session.close()

def fetch_categories():
    session = Session()
    try:
        categories = session.query(Pathway.category).distinct().all()
        return [category[0] for category in categories]
    finally:
        session.close()

# Add a job posting to the database
def add_job_posting_to_db(job_pathway):
    session = Session()
    try:
        # Create a new Pathway object for the job posting
        pathway = Pathway(
            id=job_pathway['id'],
            name=job_pathway['name'],
            category=job_pathway['category'],
            description=job_pathway['description'],
            target_customers=job_pathway['target_customers'],
            success_examples=job_pathway['success_examples'],
            key_skills=job_pathway['key_skills'],
            metrics=job_pathway['metrics'],
            rationale=job_pathway['rationale'],
            is_job_posting=True,
            job_data=job_pathway.get('job_data', {})
        )
        
        # Add the pathway to the database
        session.add(pathway)
        
        # Extract and add skills to the skills database
        add_skills_from_job(session, job_pathway)
        
        session.commit()
        print(f"Successfully added job posting {job_pathway['name']} to database")
        return True
    except Exception as e:
        session.rollback()
        print(f"Error adding job posting to database: {e}")
        return False
    finally:
        session.close()

# Extract and add skills from a job posting
def add_skills_from_job(session, job_pathway):
    job_data = job_pathway.get('job_data', {})
    if not job_data:
        return
    
    job_id = job_pathway['id']
    job_title = job_data.get('job_title', 'Unknown Position')
    category = job_pathway['category']
    
    # Process required skills
    required_skills = job_data.get('required_skills', []) or []
    if required_skills:
        for skill_name in required_skills:
            if not skill_name:
                continue
                
            # Check if this skill already exists
            existing_skill = session.query(JobSkill).filter(
                JobSkill.name == skill_name,
                JobSkill.job_id == job_id,
                JobSkill.skill_type == 'required'
            ).first()
            
            if existing_skill:
                # Increment the frequency
                existing_skill.frequency += 1
            else:
                # Add a new skill
                skill = JobSkill(
                    name=skill_name,
                    skill_type='required',
                    job_id=job_id,
                    job_title=job_title,
                    category=category
                )
                session.add(skill)
    
    # Process preferred skills
    preferred_skills = job_data.get('preferred_skills', []) or []
    if preferred_skills:
        for skill_name in preferred_skills:
            if not skill_name:
                continue
                
            # Check if this skill already exists
            existing_skill = session.query(JobSkill).filter(
                JobSkill.name == skill_name,
                JobSkill.job_id == job_id,
                JobSkill.skill_type == 'preferred'
            ).first()
            
            if existing_skill:
                # Increment the frequency
                existing_skill.frequency += 1
            else:
                # Add a new skill
                skill = JobSkill(
                    name=skill_name,
                    skill_type='preferred',
                    job_id=job_id,
                    job_title=job_title,
                    category=category
                )
                session.add(skill)

# Fetch job skills from the database
def fetch_job_skills(top_n=None, skill_type=None, category=None):
    session = Session()
    try:
        # Base query
        query = session.query(JobSkill)
        
        # Apply filters
        if skill_type:
            query = query.filter(JobSkill.skill_type == skill_type)
        if category:
            query = query.filter(JobSkill.category == category)
        
        # Get results
        skills = query.all()
        
        # Aggregate frequencies for the same skill
        skill_freq = {}
        for skill in skills:
            skill_name = skill.name.lower()
            if skill_name in skill_freq:
                skill_freq[skill_name]['frequency'] += skill.frequency
                skill_freq[skill_name]['jobs'].add(skill.job_id)
            else:
                skill_freq[skill_name] = {
                    'name': skill.name,
                    'frequency': skill.frequency,
                    'jobs': {skill.job_id}
                }
        
        # Convert to list and sort by frequency
        result = [
            {
                'name': info['name'],
                'frequency': info['frequency'],
                'job_count': len(info['jobs'])
            }
            for skill_name, info in skill_freq.items()
        ]
        result.sort(key=lambda x: x['frequency'], reverse=True)
        
        # Limit to top N if specified
        if top_n:
            result = result[:top_n]
            
        return result
    finally:
        session.close()

# Initialize the database and import data
def init_and_load_data():
    init_db()
    import_simpler_data()
    
    # Return the data in the format expected by the application
    pathways_data = fetch_pathways()
    metrics_data = fetch_metrics()
    categories = fetch_categories()
    
    # Convert to DataFrame to maintain compatibility with existing code
    pathways_df = pd.DataFrame(pathways_data)
    
    return pathways_df, metrics_data, categories

# Test if database connection is working
def test_connection():
    try:
        conn = engine.connect()
        conn.close()
        return True
    except Exception as e:
        print(f"Database connection error: {e}")
        return False

if __name__ == "__main__":
    if test_connection():
        print("Database connection successful")
        init_and_load_data()
    else:
        print("Failed to connect to database")