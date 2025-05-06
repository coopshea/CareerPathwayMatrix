import os
import json
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Float, JSON, MetaData, Table, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

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
            'rationale': self.rationale
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