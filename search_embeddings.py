import os
import numpy as np
import pandas as pd
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity

client = OpenAI()

# Load embeddings data from CSV
embeddings_df = pd.read_csv("embeddings.csv")

def generate_query_embedding(query, model="text-embedding-3-small"):
    """Generate an embedding for a search query."""
    try:
        response = client.embeddings.create(
            input=[query],
            model=model
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error generating query embedding: {e}")
        return None

def search(query, top_n=5):
    """Find the top N most similar text chunks to the query."""
    query_embedding = generate_query_embedding(query)
    if query_embedding is None:
        print("Query embedding generation failed.")
        return []
    
    # Convert embeddings in the CSV to numpy arrays
    embeddings = embeddings_df['embedding'].apply(eval).apply(np.array).tolist()
    
    # Calculate cosine similarity between query embedding and each chunk's embedding
    similarities = cosine_similarity([query_embedding], embeddings)[0]

    # Add similarities to the DataFrame and sort by similarity
    embeddings_df['similarity'] = similarities
    top_results = embeddings_df.sort_values(by='similarity', ascending=False).head(top_n)

    # Return the top matching results
    return top_results[['filename', 'text', 'similarity']]


'''     
# Example usage hard coded 
query = "How to manage high blood pressure?"
results = search(query)
print("Top search results:")
print(results)
''' 


# Example 2 Ask for the query in the terminal
query = input("Please enter your question: ")

# Run the search and display the top 3 results
results = search(query, top_n=3)
print("\nTop 3 search results:")
print(results[['filename', 'text', 'similarity']])