from openai import OpenAI
from sqlalchemy import create_engine, select, Column, Integer, String, JSON, TIMESTAMP
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import UserDefinedType
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize the client with your API key
client = OpenAI()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define a custom VECTOR type
class Vector(UserDefinedType):
    def get_col_spec(self):
        return "VECTOR(1536)"

# Define Document model to match 'documents' table
class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(TIMESTAMP)
    url = Column(String)
    title = Column(String)
    headings = Column(JSON)
    paragraphs = Column(JSON)
    lists = Column(JSON)
    links = Column(JSON)
    embedding = Column(Vector)  # Use custom Vector type

# Function to fetch transcription text from database
def fetch_transcription_text(session):
    """Fetch text data from the database to use as context."""
    # Query the database to get the most recent document (or any document as needed)
    document = session.query(Document).order_by(Document.timestamp.desc()).first()
    
    if document:
        # Combine fields to create a context similar to the transcription text
        transcription_text = " ".join([
            document.title or "",
            " ".join(document.headings.get("h1", [])),
            " ".join(document.headings.get("h2", [])),
            " ".join(document.headings.get("h3", [])),
            " ".join(document.paragraphs or [])
        ])
        return transcription_text
    else:
        print("No documents found in the database.")
        return ""

# Function to start and maintain an ongoing conversation
def ongoing_conversation(transcription_text):
    """
    Start a conversation with GPT-4o, maintaining the conversation history efficiently.
    
    Parameters:
    transcription_text (str): The initial context for the assistant to refer to.
    
    Returns:
    None
    """
    # Messages list to hold the conversation history
    messages = [
        {"role": "system", "content": "You are a helpful assistant. Your job is to answer the user's questions based ONLY on the provided context."},
        {"role": "system", "content": f"Context: {transcription_text}"}
    ]

    print("What would you like to ask Avatar Peter today?. Type 'exit', 'quit', or 'bye' to end the conversation.")
    while True:
        # Get user input
        user_input = input("You: ")

        # Check if the user wants to exit
        if user_input.lower() in ['exit', 'quit', 'bye']:
            print("Avatar Peter: Goodbye!")
            break

        # Append the user's message to the conversation history
        messages.append({"role": "user", "content": user_input})

        # Get the assistant's response using OpenAI API
        try:
            completion = client.chat.completions.create(
                model="gpt-4o", 
                messages=messages
            )

            # Extract the response
            assistant_response = completion.choices[0].message.content
            print(f"Avatar Peter: {assistant_response}")

            # Append the assistant's response to the conversation history
            messages.append({"role": "assistant", "content": assistant_response})

        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Initialize a session to interact with the database
    session = SessionLocal()
    
    # Fetch transcription text from the database
    transcription_text = fetch_transcription_text(session)
    
    # Close the session after fetching data
    session.close()
    
    if transcription_text:
        ongoing_conversation(transcription_text)
    else:
        print("No valid context available to start the conversation.")
