from openai import OpenAI
import pandas as pd
import os
import json 

client = OpenAI()

def generate_embeddings(text):
    """Generate embeddings for a single text chunk using OpenAI's API."""
    try:
        response = client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        # Convert response to dictionary and access embedding data
        response_data = response.to_dict()
        return response_data['data'][0]['embedding']
    except Exception as e:
        print(f"Error generating embeddings: {e}")
        return None
        return response['data'][0]['embedding']


def create_embeddings_df(directory="crawled_json"):
    """Load JSON files, generate embeddings for each text chunk, and return a DataFrame."""
    embeddings = []
    
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
        
        # Combine relevant fields into a single text string
        combined_text = " ".join([
            data.get("title", ""),
            " ".join(data.get("headings", {}).get("h1", [])),
            " ".join(data.get("headings", {}).get("h2", [])),
            " ".join(data.get("headings", {}).get("h3", [])),
            " ".join(data.get("paragraphs", []))
        ])
        
        # Generate embedding for the combined text
        embedding = generate_embeddings(combined_text)
        
        # Only add if embedding is successfully generated
        if embedding:
            embeddings.append({
                "filename": filename,
                "text": combined_text,
                "embedding": embedding
            })
    
    # Convert embeddings list to DataFrame
    embeddings_df = pd.DataFrame(embeddings)
    return embeddings_df

# Generate embeddings for each JSON file
embeddings_df = create_embeddings_df()

# Save the embeddings to a CSV file for future use
embeddings_df.to_csv("embeddings_json.csv", index=False)
print("Embeddings saved to 'embeddings_json.csv'")