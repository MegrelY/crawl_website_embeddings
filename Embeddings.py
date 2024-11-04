from openai import OpenAI
import pandas as pd
import os

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


def create_embeddings_df(chunked_df):
    """Generate embeddings for each text chunk in the DataFrame."""
    embeddings = []
    for _, row in chunked_df.iterrows():
        embedding = generate_embeddings(row['text'])
        if embedding:  # Only add if embedding is successfully generated
            embeddings.append({
                "filename": row["filename"],
                "text": row["text"],
                "embedding": embedding
            })
    
    # Convert to DataFrame
    embeddings_df = pd.DataFrame(embeddings)
    return embeddings_df

# Generate embeddings for each chunk
chunked_df = pd.read_csv("processed_chunks.csv")  # Load chunked data if saved earlier
embeddings_df = create_embeddings_df(chunked_df)

# Save the embeddings to a CSV file for future use
embeddings_df.to_csv("embeddings.csv", index=False)
print("Embeddings saved to 'embeddings.csv'")