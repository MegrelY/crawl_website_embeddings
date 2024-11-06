import os
import json
from datetime import datetime
from openai import OpenAI
from sqlalchemy import create_engine, Column, Integer, Text, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pgvector.sqlalchemy import Vector  # Correct import for vector type

# Initialize OpenAI client
client = OpenAI()

# Configure SQLAlchemy to connect to your PostgreSQL database
DATABASE_URL = "postgresql+psycopg2://postgres:mysecretpassword@localhost:5432/amp_db"
engine = create_engine(DATABASE_URL)
Base = declarative_base()

# Define the Document model to match the PostgreSQL table
class Document(Base):
    __tablename__ = 'documents'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)         # Use correct DateTime type
    url = Column(Text)
    title = Column(Text)
    headings = Column(JSON)
    paragraphs = Column(JSON)
    lists = Column(JSON)
    links = Column(JSON)
    embedding = Column(Vector(1536))  # Use Vector from pgvector.sqlalchemy

# Create the table if it doesn't exist
Base.metadata.create_all(engine)

# Set up a session
Session = sessionmaker(bind=engine)
session = Session()


def generate_embeddings(text):
    """Generate embeddings for a single text chunk using OpenAI's API."""
    try:
        response = client.embeddings.create(
            input=text,
            model="text-embedding-3-small"  # Specify your model here
        )
        # Convert response to dictionary and access embedding data
        response_data = response.to_dict()
        return response_data['data'][0]['embedding']
    except Exception as e:
        print(f"Error generating embeddings: {e}")
        return None

def migrate_data(directory="crawled_json"):
    """Read JSON files, generate embeddings, and insert data into PostgreSQL."""
    
    # Ensure the directory exists
    if not os.path.exists(directory):
        raise FileNotFoundError(f"Directory '{directory}' does not exist.")
    
    # Loop through each JSON file in the directory
    files = [f for f in os.listdir(directory) if f.endswith(".json")]
    if not files:
        raise FileNotFoundError(f"No JSON files found in directory '{directory}'.")
    
    for filename in files:
        filepath = os.path.join(directory, filename)
        
        # Load JSON content
        with open(filepath, "r", encoding="utf-8") as file:
            data = json.load(file)
        
        # Extract fields
        timestamp = datetime.fromisoformat(data.get("timestamp"))
        url = data.get("url", "")
        title = data.get("title", "")
        headings = data.get("headings", {})
        paragraphs = data.get("paragraphs", [])
        lists = data.get("lists", {})
        links = data.get("links", [])
        
        # Combine relevant fields into a single text string for embedding
        combined_text = " ".join([
            title,
            " ".join(headings.get("h1", [])),
            " ".join(headings.get("h2", [])),
            " ".join(headings.get("h3", [])),
            " ".join(paragraphs)
        ])
        
        # Generate embedding for the combined text
        embedding = generate_embeddings(combined_text)
        
        if embedding:
            # Create a new document record
            doc = Document(
                timestamp=timestamp,
                url=url,
                title=title,
                headings=headings,
                paragraphs=paragraphs,
                lists=lists,
                links=links,
                embedding=embedding
            )
            
            # Add and commit the document to the session
            session.add(doc)
            print(f"Inserted document from {filename}")

    # Commit all documents at once
    session.commit()
    print("Data migration complete.")

# Run the data migration
migrate_data()