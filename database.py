import os
import json
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Float, JSON, MetaData, Table, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
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


# User Model for authentication
class User(Base):
    __tablename__ = 'users'
    
    id = Column(String, primary_key=True)  # md5 hash of email
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    created_at = Column(Float, default=datetime.utcnow().timestamp)
    last_login = Column(Float, default=datetime.utcnow().timestamp)
    preferences = Column(JSON, default=dict)  # Store user preferences
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'created_at': self.created_at,
            'last_login': self.last_login,
            'preferences': self.preferences
        }

# User Document Model (for storing resume, etc.)
class UserDocument(Base):
    __tablename__ = 'user_documents'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey('users.id'))
    name = Column(String, nullable=False)
    doc_type = Column(String, nullable=False)  # resume, cover_letter, etc.
    content = Column(Text)  # Raw text content of document
    extracted_data = Column(JSON)  # Structured data extracted from document
    upload_date = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'doc_type': self.doc_type,
            'content': self.content[:100] + "..." if self.content and len(self.content) > 100 else self.content,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None
        }

# Chat Message Model
class ChatMessage(Base):
    __tablename__ = 'chat_messages'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey('users.id'))
    role = Column(String, nullable=False)  # user or assistant
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

class UserSkill(Base):
    __tablename__ = 'user_skills'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey('users.id'))  # New: Link to user
    name = Column(String, nullable=False, index=True)  # The skill name
    rating = Column(Integer, default=1)  # Rating from 1-5
    experience = Column(Text)  # Description of experience with this skill
    projects = Column(JSON, default=list)  # List of projects using this skill
    date_added = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'rating': self.rating,
            'experience': self.experience,
            'projects': self.projects,
            'date_added': self.date_added.isoformat() if self.date_added else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }

# Create tables if they don't exist
def init_db():
    # Check if migration is needed and perform it automatically
    try:
        if check_migration_needed():
            print("Database schema needs to be updated. Performing automatic migration...")
            recreate_tables()
            print("Automatic database migration completed successfully!")
        else:
            # If no migration is needed, just create tables as normal
            Base.metadata.create_all(engine)
    except Exception as e:
        print(f"Error during database initialization: {e}")
        # Create tables anyway in case this is a new setup
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
    """
    Fetch job skills from the database, with optional filtering.
    
    Args:
        top_n (int, optional): Limit results to the top N most frequent skills
        skill_type (str, optional): Filter by skill type ('required', 'preferred')
        category (str, optional): Filter by job category
        
    Returns:
        list: Job skills matching the criteria
    """
    # For the demo, return empty list so each user starts fresh
    return []
    try:
        session = Session()
        # Base query
        query = session.query(JobSkill)
        
        # Apply filters
        if skill_type:
            query = query.filter(JobSkill.skill_type == skill_type)
        if category:
            query = query.filter(JobSkill.category == category)
        
        # Get results
        skills = query.all()
        
        # If no skills found, add some sample skills
        if not skills:
            print("No skills found in database, adding sample skills...")
            add_sample_job_skills()
            session.close()
            
            # Create a new session and try again
            session = Session()
            query = session.query(JobSkill)
            if skill_type:
                query = query.filter(JobSkill.skill_type == skill_type)
            if category:
                query = query.filter(JobSkill.category == category)
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
                    'jobs': {skill.job_id},
                    'skill_type': skill.skill_type,
                    'job_id': skill.job_id
                }
        
        # Convert to list and sort by frequency
        result = [
            {
                'name': info['name'],
                'frequency': info['frequency'],
                'job_count': len(info['jobs']),
                'skill_type': info['skill_type'],
                'job_id': info['job_id']
            }
            for skill_name, info in skill_freq.items()
        ]
        result.sort(key=lambda x: x['frequency'], reverse=True)
        
        # Limit to top N if specified
        if top_n:
            result = result[:top_n]
            
        session.close()
        return result
    except Exception as e:
        print(f"Error fetching job skills: {e}")
        return []


# Add sample job skills to the database if no skills exist
def add_sample_job_skills():
    """
    Add sample job skills to the database if no skills exist.
    """
    try:
        session = Session()
        sample_skills = [
            {"name": "Python Programming", "skill_type": "required", "job_id": "sample_job_1", "job_title": "Data Scientist", "category": "Data Science", "frequency": 10},
            {"name": "SQL", "skill_type": "required", "job_id": "sample_job_1", "job_title": "Data Scientist", "category": "Data Science", "frequency": 8},
            {"name": "Machine Learning", "skill_type": "required", "job_id": "sample_job_1", "job_title": "Data Scientist", "category": "Data Science", "frequency": 9},
            {"name": "Data Analysis", "skill_type": "required", "job_id": "sample_job_1", "job_title": "Data Scientist", "category": "Data Science", "frequency": 7},
            {"name": "Statistics", "skill_type": "required", "job_id": "sample_job_1", "job_title": "Data Scientist", "category": "Data Science", "frequency": 6},
            {"name": "Deep Learning", "skill_type": "preferred", "job_id": "sample_job_1", "job_title": "Data Scientist", "category": "Data Science", "frequency": 5},
            
            {"name": "JavaScript", "skill_type": "required", "job_id": "sample_job_2", "job_title": "Frontend Developer", "category": "Software Development", "frequency": 10},
            {"name": "HTML", "skill_type": "required", "job_id": "sample_job_2", "job_title": "Frontend Developer", "category": "Software Development", "frequency": 9},
            {"name": "CSS", "skill_type": "required", "job_id": "sample_job_2", "job_title": "Frontend Developer", "category": "Software Development", "frequency": 9},
            {"name": "React", "skill_type": "required", "job_id": "sample_job_2", "job_title": "Frontend Developer", "category": "Software Development", "frequency": 8},
            {"name": "TypeScript", "skill_type": "preferred", "job_id": "sample_job_2", "job_title": "Frontend Developer", "category": "Software Development", "frequency": 6},
            {"name": "UI/UX Design", "skill_type": "preferred", "job_id": "sample_job_2", "job_title": "Frontend Developer", "category": "Software Development", "frequency": 5},
            
            {"name": "Java", "skill_type": "required", "job_id": "sample_job_3", "job_title": "Backend Developer", "category": "Software Development", "frequency": 9},
            {"name": "Spring Framework", "skill_type": "required", "job_id": "sample_job_3", "job_title": "Backend Developer", "category": "Software Development", "frequency": 8},
            {"name": "RESTful APIs", "skill_type": "required", "job_id": "sample_job_3", "job_title": "Backend Developer", "category": "Software Development", "frequency": 7},
            {"name": "SQL", "skill_type": "required", "job_id": "sample_job_3", "job_title": "Backend Developer", "category": "Software Development", "frequency": 7},
            {"name": "Microservices", "skill_type": "preferred", "job_id": "sample_job_3", "job_title": "Backend Developer", "category": "Software Development", "frequency": 6},
            
            {"name": "Project Management", "skill_type": "required", "job_id": "sample_job_4", "job_title": "Product Manager", "category": "Product Management", "frequency": 10},
            {"name": "Agile Methodologies", "skill_type": "required", "job_id": "sample_job_4", "job_title": "Product Manager", "category": "Product Management", "frequency": 9},
            {"name": "User Research", "skill_type": "required", "job_id": "sample_job_4", "job_title": "Product Manager", "category": "Product Management", "frequency": 8},
            {"name": "Market Analysis", "skill_type": "required", "job_id": "sample_job_4", "job_title": "Product Manager", "category": "Product Management", "frequency": 7},
            {"name": "Product Strategy", "skill_type": "required", "job_id": "sample_job_4", "job_title": "Product Manager", "category": "Product Management", "frequency": 8},
            {"name": "Data Analysis", "skill_type": "preferred", "job_id": "sample_job_4", "job_title": "Product Manager", "category": "Product Management", "frequency": 6},
        ]
        
        for skill_data in sample_skills:
            skill = JobSkill(
                name=skill_data["name"],
                skill_type=skill_data["skill_type"],
                job_id=skill_data["job_id"],
                job_title=skill_data["job_title"],
                category=skill_data["category"],
                frequency=skill_data["frequency"]
            )
            session.add(skill)
        
        try:
            session.commit()
            print("Added sample job skills to database")
        except Exception as e:
            session.rollback()
            print(f"Error adding sample job skills: {e}")
    except Exception as e:
        print(f"Error in add_sample_job_skills: {e}")
    finally:
        session.close()


# Functions for user skills management
def save_user_skills(skills_dict):
    """
    Save user skills to the database.
    
    Args:
        skills_dict (dict): Dictionary of user skills to save
            {skill_name: {rating, experience, projects}}
    
    Returns:
        bool: Success or failure
    """
    # Import here to avoid circular imports
    import uuid
    import streamlit as st
    from user_auth import is_authenticated, get_username
    
    # Get user ID - either from auth or create temporary session ID
    if is_authenticated():
        user_id = get_username()
    else:
        # Create and store a temporary user ID in session state
        if "temp_user_id" not in st.session_state:
            st.session_state.temp_user_id = str(uuid.uuid4())
        user_id = st.session_state.temp_user_id
    
    session = None
    try:
        session = Session()
        
        # Only delete skills for THIS user, not all users
        session.query(UserSkill).filter(UserSkill.user_id == user_id).delete()
        
        # Add new skills with the user ID
        for skill_name, skill_data in skills_dict.items():
            skill = UserSkill(
                user_id=user_id,  # Associate with specific user
                name=skill_name,
                rating=skill_data.get('rating', 1),
                experience=skill_data.get('experience', ''),
                projects=skill_data.get('projects', [])
            )
            session.add(skill)
        
        session.commit()
        print(f"Saved {len(skills_dict)} user skills to database for user {user_id}")
        return True
    except Exception as e:
        session.rollback()
        print(f"Error saving user skills to database: {e}")
        return False
    finally:
        session.close()


def fetch_user_skills(user_id=None):
    """
    Fetch user skills from the database for a specific user.
    
    Args:
        user_id (str, optional): User ID to fetch skills for
    
    Returns:
        dict: Dictionary of user skills
            {skill_name: {rating, experience, projects}}
    """
    # Import here to avoid circular imports
    import uuid
    import streamlit as st
    from user_auth import is_authenticated, get_username
    
    if not user_id:
        # For authenticated users, use their username as ID
        if is_authenticated():
            user_id = get_username()
        else:
            # For demo, create session-specific ID
            if "temp_user_id" not in st.session_state:
                st.session_state.temp_user_id = str(uuid.uuid4())
            user_id = st.session_state.temp_user_id
    
    session = None
    try:
        session = Session()
        # Query skills only for this specific user
        skills = session.query(UserSkill).filter(UserSkill.user_id == user_id).all()
        
        # Convert to dictionary
        skills_dict = {}
        for skill in skills:
            skills_dict[skill.name] = {
                'rating': skill.rating,
                'experience': skill.experience,
                'projects': skill.projects
            }
        
        return skills_dict
    except Exception as e:
        print(f"Error fetching user skills from database: {e}")
        return {}
    finally:
        if session:
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

# Recreate the database tables (use with caution, will delete all data)
def recreate_tables():
    session = Session()
    try:
        # Drop the existing tables
        print("Dropping existing tables...")
        Base.metadata.drop_all(engine)
        
        # Create the tables with the new schema
        print("Creating tables with new schema...")
        Base.metadata.create_all(engine)
        
        # Import the original data
        print("Importing data...")
        import_simpler_data()
        
        print("Database tables have been recreated successfully!")
        return True
    except Exception as e:
        session.rollback()
        print(f"Error recreating tables: {e}")
        return False
    finally:
        session.close()

# Check if the database needs migration
def check_migration_needed():
    session = Session()
    try:
        # Try to query and see if the new columns exist
        try:
            session.query(Pathway.is_job_posting).first()
            # If we get here, the column exists
            return False
        except Exception:
            # If we get an error, the column doesn't exist and migration is needed
            return True
    finally:
        session.close()

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
        
        # Check if migration is needed and perform it if necessary
        if check_migration_needed():
            print("Database schema needs to be updated...")
            if recreate_tables():
                print("Database schema has been updated successfully.")
            else:
                print("Failed to update the database schema.")
        else:
            print("Database schema is up to date.")
            
        init_and_load_data()
    else:
        print("Failed to connect to database")